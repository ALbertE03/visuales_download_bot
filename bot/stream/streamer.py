import logging
import math
from collections import OrderedDict
from typing import AsyncGenerator, Optional

from pyrogram import Client, raw
from pyrogram.file_id import FileId, FileType, PHOTO_TYPES

from bot.stream.config import StreamConfig
from bot.stream.file_properties import FileInfo, get_file_info_by_id

logger = logging.getLogger(__name__)


class PyrogramStreamer:
    """Descarga chunks de archivos de Telegram para streaming HTTP."""

    def __init__(self, client: Client):
        self.client = client
        self.cached_files: OrderedDict[int, FileInfo] = OrderedDict()

    async def get_file_properties(self, message_id: int) -> Optional[FileInfo]:
        """Obtiene las propiedades de un archivo, con caché."""
        if message_id in self.cached_files:
            return self.cached_files[message_id]

        file_info = await get_file_info_by_id(
            self.client, StreamConfig.BIN_CHANNEL, message_id
        )
        if not file_info:
            logger.debug("Archivo no encontrado para message_id %s", message_id)
            return None

        if len(self.cached_files) >= StreamConfig.CACHE_SIZE:
            self.cached_files.popitem(last=False)

        self.cached_files[message_id] = file_info
        logger.debug("FileInfo cacheado para message_id %s", message_id)
        return file_info

    async def download(
        self,
        file_info: FileInfo,
        file_size: int,
        from_bytes: int,
        until_bytes: int,
    ) -> AsyncGenerator[bytes, None]:
        """
        Descarga un rango de bytes de un archivo de Telegram.

        Usa la API raw de Pyrogram con manejo automático de DCs.
        Soporta Range requests para seeking en videos.
        """
        chunk_size = StreamConfig.CHUNK_SIZE  # 1MB

        file_id = FileId.decode(file_info.file_id)
        dc_id = file_id.dc_id

        if file_id.file_type in PHOTO_TYPES:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size or "y",
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size or "",
            )

        # Calcular los chunks necesarios
        offset = from_bytes - (from_bytes % chunk_size)
        first_part_cut = from_bytes - offset
        first_part = math.floor(offset / chunk_size)
        last_part_cut = until_bytes % chunk_size + 1
        last_part = math.ceil(until_bytes / chunk_size)
        part_count = last_part - first_part
        total_parts = math.ceil(file_size / chunk_size)

        logger.debug(
            "Streaming: chunks %s-%s de %s (total %s)",
            first_part,
            last_part,
            part_count,
            total_parts,
        )

        try:
            # Obtener sesión para el DC correcto
            logger.debug(f"Conectando al DC {dc_id}...")
            session = await self.client.get_session(dc_id, is_media=True)
            
            # Asegurar conexión
            if not session.is_connected:
                await session.connect()

            current_part = 1
            current_offset = offset

            logger.debug(f"Iniciando petición raw a Telegram (offset: {offset})")

            while current_part <= part_count:
                result = await session.invoke(
                    raw.functions.upload.GetFile(
                        location=location,
                        offset=current_offset,
                        limit=chunk_size,
                    ),
                    sleep_threshold=30,
                )

                if not isinstance(result, raw.types.upload.File) or not result.bytes:
                    break

                chunk = result.bytes
                current_offset += chunk_size

                # Recortar el primer y último chunk
                if part_count == 1:
                    yield chunk[first_part_cut:last_part_cut]
                elif current_part == 1:
                    yield chunk[first_part_cut:]
                elif current_part == part_count:
                    yield chunk[:last_part_cut]
                else:
                    yield chunk

                logger.info(
                    "Chunk %s/%s descargado (total %s)",
                    current_part,
                    last_part,
                    total_parts,
                )
                current_part += 1

            logger.info("Streaming completado")

        except (GeneratorExit, StopAsyncIteration):
            logger.debug("Streaming interrumpido por el cliente")
            raise
        except Exception:
            logger.error("Error durante el streaming", exc_info=True)
