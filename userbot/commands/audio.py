from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message
from bot.log import logger
from userbot.core.transcription import process_transcription

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

async def auto_transcribe_private(client: Client, message: Message):
    logger.info(f"Transcripción automática activada en PV: {message.chat.id}")
    await process_transcription(client, message)