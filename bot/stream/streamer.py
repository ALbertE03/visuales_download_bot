import logging
import math
import asyncio
from collections import OrderedDict
from typing import AsyncGenerator, Optional

from pyrogram import Client, raw
from pyrogram.file_id import FileId, PHOTO_TYPES

from bot.stream.config import StreamConfig
from bot.stream.file_properties import FileInfo, get_file_info_by_id
from bot.stream.cache import global_chunk_cache, global_coordinator
from bot.stream.prefetch import global_prefetch_manager

logger = logging.getLogger("visuales_bot")

class PyrogramStreamer:
    """Descarga chunks de archivos de Telegram para streaming HTTP, usando cache y preloading."""

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
        chunk_size = StreamConfig.CHUNK_SIZE

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

        offset = from_bytes - (from_bytes % chunk_size)
        first_part_cut = from_bytes - offset
        first_part = math.floor(offset / chunk_size)
        last_part_cut = until_bytes % chunk_size + 1
        last_part = math.ceil(until_bytes / chunk_size)
        part_count = last_part - first_part
        total_parts = math.ceil(file_size / chunk_size)
        
        prefetch_count = StreamConfig.PREFETCH_COUNT

        logger.debug(
            "Streaming: chunks %s-%s de %s (total %s)",
            first_part, last_part, part_count, total_parts,
        )

        try:
            session = None
            current_part = 1
            current_offset = offset
            
            # Rate limiting logic
            import time
            start_time = time.time()
            bytes_sent = 0
            avg_bytes_per_sec = 0
            buffer_bytes = 0
            if getattr(file_info, "duration", 0) and file_info.duration > 0:
                avg_bytes_per_sec = file_info.file_size / file_info.duration
                buffer_bytes = avg_bytes_per_sec * 60  # 1 minute buffer

            while current_part <= part_count:
                chunk = await global_chunk_cache.get(file_info.file_id, current_offset)
                
                if not chunk:
                    should_download = await global_coordinator.wait_or_start(file_info.file_id, current_offset)
                    if should_download:
                        try:
                            if not session:
                                session = await self.client.get_session(dc_id, is_media=True)
                            
                            result = await session.invoke(
                                raw.functions.upload.GetFile(
                                    location=location,
                                    offset=current_offset,
                                    limit=chunk_size,
                                ),
                                sleep_threshold=StreamConfig.SLEEP_THRESHOLD,
                            )
                            if isinstance(result, raw.types.upload.File) and result.bytes:
                                chunk = result.bytes
                                await global_chunk_cache.put(file_info.file_id, current_offset, chunk)
                            else:
                                break
                        except Exception:
                            logger.error("Error obteniendo bloque de Telegram", exc_info=True)
                            await global_coordinator.finish(file_info.file_id, current_offset)
                            break
                        finally:
                            await global_coordinator.finish(file_info.file_id, current_offset)
                    else:
                        chunk = await global_chunk_cache.get(file_info.file_id, current_offset)
                
                if not chunk:
                    break
                
                # Iniciar prefetch de los siguientes bloques (1 minuto aprox)
                if current_part == 1 or current_part % 5 == 0:
                    prefetch_start_offset = current_offset + chunk_size
                    prefetch_start_part = first_part + current_part
                    if prefetch_start_offset < file_size:
                        global_prefetch_manager.start_prefetch(
                            self.client, dc_id, file_info.file_id, location,
                            prefetch_start_offset, prefetch_start_part, prefetch_count,
                            chunk_size, file_size
                        )

                current_offset += chunk_size

                chunk_to_yield = chunk
                if part_count == 1:
                    chunk_to_yield = chunk[first_part_cut:last_part_cut]
                elif current_part == 1:
                    chunk_to_yield = chunk[first_part_cut:]
                elif current_part == part_count:
                    chunk_to_yield = chunk[:last_part_cut]

                # Rate limiting 
                if avg_bytes_per_sec > 0:
                    elapsed = time.time() - start_time
                    expected_bytes_played = avg_bytes_per_sec * elapsed
                    if bytes_sent > expected_bytes_played + buffer_bytes:
                        sleep_time = (bytes_sent - buffer_bytes - expected_bytes_played) / avg_bytes_per_sec
                        if sleep_time > 0:
                            import asyncio
                            await asyncio.sleep(min(sleep_time, 5.0))
                
                bytes_sent += len(chunk_to_yield)
                yield chunk_to_yield

                current_part += 1

        except (GeneratorExit, StopAsyncIteration):
            logger.debug("Streaming interrumpido por el cliente")
            raise
        except Exception:
            logger.error("Error durante el streaming", exc_info=True)
