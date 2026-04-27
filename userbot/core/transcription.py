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