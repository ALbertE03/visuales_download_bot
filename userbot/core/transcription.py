import os
import asyncio
import requests
import streamlit as st
from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message
from bot.log import logger

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

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

async def _notify_error(client: Client, response_msg: Message, err_desc: str):
    logger.error(f"Transcripción Error: {err_desc}")
    if response_msg:
        try:
            await response_msg.delete()
        except Exception:
            pass
    try:
        await client.send_message("me", f"❌ <b>Error en Transcripción:</b>\n<pre>{err_desc}</pre>")
    except Exception as ex:
        logger.error(f"No se pudo notificar el error a 'me': {ex}")

async def process_transcription(
    client: Client, media_msg: Message, response_msg: Message = None
):
    """
    Función central para procesar transcripciones.
    Si hay un error y response_msg (el /totext) existe, lo borra y advierte en Saved Messages ("me").
    """
    if not GROQ_API_KEY:
        await _notify_error(client, response_msg, "Falta GROQ_API_KEY en .streamlit/secrets.toml")
        return

    file_path = await client.download_media(media_msg)
    if not file_path:
        await _notify_error(client, response_msg, "No se pudo descargar el archivo multimedia.")
        return
        
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
            await _notify_error(client, response_msg, f"Error en Groq ({response.status_code}): {response.text}")

    except Exception as e:
        await _notify_error(client, response_msg, f"Excepción interna: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Archivo temporal eliminado: {file_path}")
