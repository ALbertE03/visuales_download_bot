import asyncio
import logging
from typing import Set
from pyrogram import Client, raw
from bot.stream.config import StreamConfig
from bot.stream.cache import global_chunk_cache, global_coordinator

logger = logging.getLogger("visuales_bot")

class PrefetchManager:
    def __init__(self):
        self.active_tasks: Set[asyncio.Task] = set()
        
    def start_prefetch(self, client: Client, dc_id: int, file_id_str: str, location, offset: int, start_part: int, part_count: int, chunk_size: int, file_size: int):
        task = asyncio.create_task(
            self._prefetch_worker(client, dc_id, file_id_str, location, offset, start_part, part_count, chunk_size, file_size)
        )
        self.active_tasks.add(task)
        task.add_done_callback(self.active_tasks.discard)
        
    async def _prefetch_worker(self, client: Client, dc_id: int, file_id_str: str, location, start_offset: int, start_part: int, part_count: int, chunk_size: int, file_size: int):
        try:
            session = await client.get_session(dc_id, is_media=True)
            current_offset = start_offset
            
            for _ in range(start_part, start_part + part_count):
                if current_offset >= file_size:
                    break
                    
                cached_chunk = await global_chunk_cache.get(file_id_str, current_offset)
                if not cached_chunk:
                    should_download = await global_coordinator.wait_or_start(file_id_str, current_offset)
                    if should_download:
                        try:
                            result = await session.invoke(
                                raw.functions.upload.GetFile(
                                    location=location,
                                    offset=current_offset,
                                    limit=chunk_size,
                                ),
                                sleep_threshold=StreamConfig.SLEEP_THRESHOLD,
                            )
                            if isinstance(result, raw.types.upload.File) and result.bytes:
                                await global_chunk_cache.put(file_id_str, current_offset, result.bytes)
                        except Exception as e:
                            logger.error(f"Error en prefetch de offset {current_offset}: {e}")
                        finally:
                            await global_coordinator.finish(file_id_str, current_offset)
                current_offset += chunk_size
        except Exception as e:
            logger.debug(f"Prefetch abortado/fallo: {e}")

global_prefetch_manager = PrefetchManager()
