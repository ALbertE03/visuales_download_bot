

import logging
from pyrogram import Client
from pyrogram.types import Message
from bot.stream.config import StreamConfig
from bot.stream.file_properties import get_file_info, pack_file, get_short_hash

logger = logging.getLogger(__name__)

STREAMABLE_MIMES = {"video", "audio"}


async def stream_handler(client: Client, message: Message):
    """Maneja el comando /stream o archivos enviados para streaming."""

    if not message.reply_to_message and not _has_media(message):
        await message.reply(
            "<blockquote><b>Uso:</b> Envía un archivo y responde con "
            "<code>/stream</code>, o reenvía un archivo al bot.</blockquote>",
        )
        return

    target = message.reply_to_message if message.reply_to_message else message

    if not _has_media(target):
        await message.reply(
            "<blockquote><b>Error:</b> El mensaje no contiene un archivo.</blockquote>"
        )
        return

    try:
        status_msg = await message.reply(
            "<blockquote><i>Generando enlace de stream...</i></blockquote>"
        )

        forwarded = await target.forward(StreamConfig.BIN_CHANNEL)

        file_info = get_file_info(forwarded)
        if not file_info:
            await status_msg.edit_text(
                "<blockquote><b>Error:</b> No se pudo obtener info del archivo.</blockquote>"
            )
            return

        # Generar hash y link
        full_hash = pack_file(
            file_info.file_name,
            file_info.file_size,
            file_info.mime_type,
            file_info.message_id,
        )
        file_hash = get_short_hash(full_hash)
        stream_link = f"{StreamConfig.URL}stream/{forwarded.id}?hash={file_hash}"

        # Determinar si es media reproducible
        is_media = any(m in (file_info.mime_type or "") for m in STREAMABLE_MIMES)

       
        if is_media:
            text = f"\n<code>{stream_link}</code>"
        else:
            text = f"🔗 <code>{stream_link}</code>"

        await status_msg.edit_text(
            text
        )



        logger.info("Stream link generado: %s (msg_id=%s)", stream_link, forwarded.id)

    except Exception as e:
        logger.error("Error generando stream link: %s", e, exc_info=True)
        await message.reply(f"<blockquote><b>Error:</b>\n<pre>{e}</pre></blockquote>")


async def stream_media_handler(client: Client, message: Message):
    """Handler para archivos enviados directamente al bot (sin /stream)."""
    await stream_handler(client, message)


def _has_media(message: Message) -> bool:
    """Verifica si un mensaje tiene media que se pueda streamear."""
    return bool(
        message.document
        or message.video
        or message.audio
        or message.photo
        or message.voice
        or message.video_note
    )
