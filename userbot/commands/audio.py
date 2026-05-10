from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message
from bot.log import logger
from userbot.const import CONST
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
    if not message.chat:
        pass
    else:
        username_lower = (message.chat.username or "").lower()
        from_username_lower = (message.from_user.username or "").lower() if message.from_user else ""
        forward_username_lower = (message.forward_from.username or "").lower() if message.forward_from else ""
        excluded_list = [u.lower() for u in CONST.CHAT_NOT_INCLUDED]

        if (username_lower in excluded_list or 
            from_username_lower in excluded_list or 
            forward_username_lower in excluded_list):
            logger.info(
                f"Transcripción automática omitida para: {username_lower or from_username_lower or forward_username_lower}"
            )
            return

    logger.info(f"Transcripción automática activada en PV: {message.chat.id}")
    await process_transcription(client, message)
