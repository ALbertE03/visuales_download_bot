import asyncio
from collections import OrderedDict
from typing import Dict, Tuple, Optional

from bot.stream.config import StreamConfig

class ChunkCache:
    def __init__(self, max_size_bytes: int = StreamConfig.MAX_CACHE_BYTES):
        self.max_size_bytes = max_size_bytes
        self.current_size = 0
        self.cache: OrderedDict[Tuple[str, int], bytes] = OrderedDict()
        self.lock = asyncio.Lock()
        
    async def get(self, file_id: str, offset: int) -> Optional[bytes]:
        async with self.lock:
            key = (file_id, offset)
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
            
    async def put(self, file_id: str, offset: int, data: bytes):
        async with self.lock:
            key = (file_id, offset)
            if key in self.cache:
                return
            
            data_len = len(data)
            while self.current_size + data_len > self.max_size_bytes and self.cache:
                _, removed_data = self.cache.popitem(last=False)
                self.current_size -= len(removed_data)
                
            self.cache[key] = data
            self.current_size += data_len

class DownloadCoordinator:
    def __init__(self):
        self.in_progress: Dict[Tuple[str, int], asyncio.Event] = {}
        self.lock = asyncio.Lock()
        
    async def wait_or_start(self, file_id: str, offset: int) -> bool:
        key = (file_id, offset)
        event = None
        async with self.lock:
            if key in self.in_progress:
                event = self.in_progress[key]
            else:
                self.in_progress[key] = asyncio.Event()
                return True
        await event.wait()
        return False
        
    async def finish(self, file_id: str, offset: int):
        key = (file_id, offset)
        async with self.lock:
            if key in self.in_progress:
                self.in_progress[key].set()
                del self.in_progress[key]

global_chunk_cache = ChunkCache()
global_coordinator = DownloadCoordinator()
