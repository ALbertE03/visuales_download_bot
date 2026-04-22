import os
import asyncio
import requests
import streamlit as st
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message
from bot.log import logger

API_ID = st.secrets.get("API_ID")
API_HASH = st.secrets.get("API_HASH")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
HF_API_KEY = st.secrets.get("HF_API_KEY")
SESSION_STRING = st.secrets.get("SESSION_STRING", "")
processed_cine_msgs = set()

if not API_ID or not API_HASH:
    print("Falta el API_ID o API_HASH en los secretos de Streamlit (secrets.toml)")
    exit(1)


if SESSION_STRING:
    userbot_app = Client("my_userbot", session_string=SESSION_STRING, api_id=int(API_ID), api_hash=API_HASH, in_memory=True)
else:
    userbot_app = Client("my_userbot", api_id=int(API_ID), api_hash=API_HASH, workdir="userbot")


def query_hf_api(api_url, payload):
    """Llama a la Inference API de Hugging Face de forma general"""
    if not HF_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    return requests.post(api_url, headers=headers, json=payload, timeout=120)

def translate_to_spanish(text):
    """Traduce texto al español usando la API pública de Google Translate"""
    if not text:
        return ""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": "es", "dt": "t", "q": text}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            res = r.json()
            translated_parts = [part[0] for part in res[0] if part[0]]
            return "".join(translated_parts)
        return text
    except Exception:
        return text


async def process_transcription(
    client: Client, media_msg: Message, response_msg: Message = None
):
    """
    Función central para procesar transcripciones.
    Si response_msg existe, lo edita. Si no, responde al media_msg.
    """
    if not GROQ_API_KEY:
        error_txt = "Falta GROQ_API_KEY en .env"
        if response_msg:
            try:
                await response_msg.edit_text(error_txt)
            except MessageNotModified:
                pass
        else:
            await media_msg.reply_text(error_txt)
        return

    file_path = await client.download_media(media_msg)
    logger.info(f"Audio descargado en: {file_path}")
    try:
        with open(file_path, "rb") as audio_file:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            data = {"model": "whisper-large-v3", "response_format": "json"}
            files = {"file": (os.path.basename(file_path), audio_file)}

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, headers=headers, data=data, files=files),
            )

        if response.status_code == 200:
            text_transcribed = response.json().get("text", "")
            if not text_transcribed:
                final_text = "No se detectó texto."
                logger.info("Transcripción vacía recibida de Groq.")
            else:
                logger.info("Transcripción exitosa:")
                translated_text = await loop.run_in_executor(
                    None, lambda: translate_to_spanish(text_transcribed)
                )
                final_text = translated_text if translated_text else text_transcribed
                if text_transcribed.strip().lower() == translated_text.strip().lower():
                    final_text = text_transcribed

            if response_msg:
                try:
                    await response_msg.edit_text(final_text)
                except MessageNotModified:
                    pass
            else:
                await media_msg.reply_text(final_text)
        else:
            err_msg = f"Error en Groq: {response.status_code}"
            logger.error(f"Error en API Groq ({response.status_code}): {response.text}")
            if response_msg:
                try:
                    await response_msg.edit_text(err_msg)
                except MessageNotModified:
                    pass
            else:
                await media_msg.reply_text(err_msg)

    except Exception as e:
        logger.exception(f"Excepción durante la transcripción: {e}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Archivo temporal eliminado: {file_path}")


@userbot_app.on_message(filters.command("totext", prefixes="/") & filters.me)
async def totext_cmd(client: Client, message: Message):
    target = message.reply_to_message
    if not target or not (
        target.voice
        or target.video_note
        or (target.document and "audio" in target.document.mime_type)
        or target.audio
    ):
        try:
            await message.edit_text("Responde a un audio para transcribir.")
        except MessageNotModified:
            pass
        return
    logger.info(f"Comando /totext activado por usuario en {message.chat.id}")
    await process_transcription(client, target, response_msg=message)


@userbot_app.on_message(
    filters.private
    & ~filters.me
    & (
        filters.voice
        | filters.video_note
        | filters.audio
        | (filters.document & filters.regex(r"audio/.*"))
    )
)
async def auto_transcribe_private(client: Client, message: Message):
    logger.info(f"Transcripción automática activada en PV: {message.chat.id}")
    await process_transcription(client, message)

@userbot_app.on_message(filters.command("img", prefixes="/") & filters.me)
async def imagine_cmd(client: Client, message: Message):
    if not HF_API_KEY:
        logger.error("Falta configurar HF_API_KEY en los secretos.")
        await message.delete()
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.edit_text("Uso correcto: `/img <describe tu imagen aquí>`")
        return
    
    prompt = parts[1]
    await message.edit_text(f"Generando imagen: <i>{prompt}</i>\nEsto puede tardar un poco...")

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    
    loop = asyncio.get_event_loop()
    try:
        for attempt in range(2):
            res = await loop.run_in_executor(None, lambda: query_hf_api(API_URL, {"inputs": prompt}))
            
            if res and res.status_code == 200:
                img_io = BytesIO(res.content)
                img_io.name = "image.png"
                await message.reply_photo(photo=img_io, caption=f"✨ <b>Prompt:</b> {prompt}")
                await message.delete()
                return
            elif res and res.status_code == 503 and attempt == 0:
                logger.info("Modelo de Hugging Face durmiendo (HTTP 503). Esperando 60 segundos para reintentar...")
                await asyncio.sleep(60)
                continue
            
          
            err = res.text if res else "No response"
            logger.error(f"Error generando imagen en HF API ({res.status_code if res else 'Unknown'}): {err}")
            await message.delete()
            return
            
    except Exception as e:
        logger.exception(f"Excepción en el generador de imágenes: {e}")
        await message.delete()



@userbot_app.on_message(filters.chat("chat1080p") & filters.regex(r"(?i)^#cine") & ~filters.me)
async def cine_filter_handler(client: Client, message: Message):

    if message.id in processed_cine_msgs:
        return
    processed_cine_msgs.add(message.id)
    
    if len(processed_cine_msgs) > 500:
        processed_cine_msgs.clear()
        
    if not message.text and not message.caption:
        return
        
    if not message.photo and not message.document:
        await message.reply_text("es con una foto")
