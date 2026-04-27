from dataclasses import dataclass
import hashlib
from typing import Optional
from pyrogram import Client
from pyrogram.types import Message
from bot.stream.config import StreamConfig


@dataclass
class FileInfo:
    """Información de un archivo de Telegram necesaria para el streaming."""

    __slots__ = ("file_size", "mime_type", "file_name", "file_id", "message_id")

    file_size: int
    mime_type: str
    file_name: str
    file_id: str  # Pyrogram file_id string (codifica DC, access_hash, etc.)
    message_id: int


def get_file_info(message: Message) -> Optional[FileInfo]:
    """Extrae FileInfo de un mensaje de Pyrogram."""
    if message.document:
        media = message.document
        return FileInfo(
            file_size=media.file_size,
            mime_type=media.mime_type or "application/octet-stream",
            file_name=media.file_name or f"document_{message.id}",
            file_id=media.file_id,
            message_id=message.id,
        )
    elif message.video:
        media = message.video
        return FileInfo(
            file_size=media.file_size,
            mime_type=media.mime_type or "video/mp4",
            file_name=media.file_name or f"video_{message.id}.mp4",
            file_id=media.file_id,
            message_id=message.id,
        )
    elif message.audio:
        media = message.audio
        return FileInfo(
            file_size=media.file_size,
            mime_type=media.mime_type or "audio/mpeg",
            file_name=media.file_name or f"audio_{message.id}.mp3",
            file_id=media.file_id,
            message_id=message.id,
        )
    elif message.photo:
        # Tomar la resolución más alta
        photo = message.photo
        return FileInfo(
            file_size=photo.file_size,
            mime_type="image/jpeg",
            file_name=f"photo_{message.id}.jpg",
            file_id=photo.file_id,
            message_id=message.id,
        )
    elif message.voice:
        media = message.voice
        return FileInfo(
            file_size=media.file_size,
            mime_type=media.mime_type or "audio/ogg",
            file_name=f"voice_{message.id}.ogg",
            file_id=media.file_id,
            message_id=message.id,
        )
    elif message.video_note:
        media = message.video_note
        return FileInfo(
            file_size=media.file_size,
            mime_type="video/mp4",
            file_name=f"videonote_{message.id}.mp4",
            file_id=media.file_id,
            message_id=message.id,
        )

    return None


async def get_file_info_by_id(
    client: Client, chat_id: int, message_id: int
) -> Optional[FileInfo]:
    """Obtiene FileInfo de un mensaje por su ID."""
    message = await client.get_messages(chat_id, message_id)
    if not message or message.empty:
        return None
    return get_file_info(message)


def pack_file(file_name: str, file_size: int, mime_type: str, message_id: int) -> str:
    """Genera un hash MD5 a partir de las propiedades del archivo."""
    hasher = hashlib.md5()
    for field in [file_name, str(file_size), mime_type, str(message_id)]:
        hasher.update(field.encode())
    return hasher.hexdigest()


def get_short_hash(full_hash: str) -> str:
    """Retorna los primeros N caracteres del hash."""
    return full_hash[: StreamConfig.HASH_LENGTH]
