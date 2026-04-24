import os
import asyncio
import requests
import streamlit as st
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.log import logger
import re
from bot.core.mongodb import db
from bot.core.search_engine import engine

API_ID = st.secrets.get("API_ID")
API_HASH = st.secrets.get("API_HASH")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
SESSION_STRING = st.secrets.get("SESSION_STRING", "")
SOURCE_CHANNEL = "CL_LibraryBK"
TARGET_GROUP_SEARCH = "chat1080p"

processed_cine_msgs = set()

if not API_ID or not API_HASH:
    print("Falta el API_ID o API_HASH en los secretos de Streamlit (secrets.toml)")
    exit(1)


if SESSION_STRING:
    userbot_app = Client(
        "my_userbot",
        session_string=SESSION_STRING,
        api_id=int(API_ID),
        api_hash=API_HASH,
        in_memory=True,
    )
else:
    userbot_app = Client(
        "my_userbot", api_id=int(API_ID), api_hash=API_HASH, workdir="userbot"
    )


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


def extract_movie_metadata(text, msg_id):
    """Extrae el título de la primera línea: Nombre | Nombre"""
    if not text:
        return None

    first_line = text.split("\n")[0]

    if "|" in first_line:
        title = first_line.split("|")[0]
    else:
        title = first_line

    title = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", title).strip()

    if not title:
        return None

    return {"msg_id": msg_id, "title": title}


async def scrape_channel_history(client: Client):
    """Escanea el historial del canal para indexar publicaciones antiguas"""
    logger.info(f"Iniciando escaneo de historial de @{SOURCE_CHANNEL}...")
    last_id = db.get_last_scanned_id(SOURCE_CHANNEL)

    count = 0
    async for message in client.get_chat_history(
        SOURCE_CHANNEL, offset_id=last_id, reverse=True
    ):
        metadata = extract_movie_metadata(message.text or message.caption, message.id)
        if metadata:
            db.save_movie(metadata)
            count += 1

        if message.id % 50 == 0:
            db.set_last_scanned_id(SOURCE_CHANNEL, message.id)

    if count > 0:
        db.set_last_scanned_id(SOURCE_CHANNEL, 0)
        engine.refresh()
        logger.info(f"Escaneo finalizado. Se indexaron {count} nuevas publicaciones.")


@userbot_app.on_message(filters.chat(SOURCE_CHANNEL))
async def auto_index_handler(client: Client, message: Message):
    """Indexa automáticamente nuevos mensajes del canal"""
    metadata = extract_movie_metadata(message.text or message.caption, message.id)
    if metadata:
        db.save_movie(metadata)
        engine.refresh()
        logger.info(f"Nueva película indexada: {metadata['title']}")


@userbot_app.on_message(filters.command("search", prefixes="/"))
async def search_handler(client: Client, message: Message):
    """Comando de búsqueda por similitud de coseno"""

    if (
        str(message.chat.id) != TARGET_GROUP_SEARCH
        and message.chat.username != TARGET_GROUP_SEARCH
    ):
        return

    query = " ".join(message.command[1:])
    if not query:
        return

    results = engine.search(query)

    if not results:
        await message.reply_text("No se encontraron resultados.")
        return

    response = f"<b>Resultados para:</b> <code>{query}</code>"
    buttons = []
    for i, res in enumerate(results, 1):
        link = f"https://t.me/{SOURCE_CHANNEL}/{res['msg_id']}"
        buttons.append([InlineKeyboardButton(f"{i}. {res['title']}", url=link)])

    await message.reply_text(
        response,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
    )


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


@userbot_app.on_message(
    filters.chat("chat1080p") & filters.regex(r"(?i)^#cine") & ~filters.me
)
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


async def startup_scraper():
    await asyncio.sleep(5)
    await scrape_channel_history(userbot_app)


asyncio.ensure_future(startup_scraper())
