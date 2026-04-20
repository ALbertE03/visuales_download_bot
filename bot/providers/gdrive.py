import re
import requests
import os
import time
import asyncio
from typing import Tuple
from bot.providers.base import BaseProvider
from bot.config import CONFIG
from bot.constants import CONSTANTS

class GDriveProvider(BaseProvider):
    def matches(self, url: str) -> bool:
        patterns = CONSTANTS.GDRIVE_PATTERNS
        return any(re.search(p, url) for p in patterns)

    def _get_file_id(self, url: str) -> str:
        patterns = CONSTANTS.GDRIVE_PATTERNS
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        file_id = self._get_file_id(url)
        if not file_id:
            raise ValueError(CONSTANTS.ERR_NO_GDRIVE_ID)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._sync_download, 
            file_id, 
            destination, 
            task_key
        )

    def _sync_download(self, file_id: str, destination: str, task_key: str) -> Tuple[str, str]:
        URL = CONSTANTS.GDRIVE_API_URL
        session = requests.Session()
        response = session.get(URL, params={'id': file_id}, stream=True)
        
        token = next((v for k, v in response.cookies.items() if k.startswith('download_warning')), None)
        if token:
            response = session.get(URL, params={'id': file_id, 'confirm': token}, stream=True)
        
        response.raise_for_status()
        
        content_disposition = response.headers.get('content-disposition', '')
        filename = re.findall('filename="(.+)"', content_disposition)
        filename = filename[0] if filename else f"gdrive_{file_id}"
            
        file_path = os.path.join(destination, filename) if os.path.isdir(destination) else destination
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        start_time = time.time()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if task_key in CONFIG.status_data.value["active"]:
                        active = CONFIG.status_data.value["active"][task_key]
                        active["downloaded"] = downloaded
                        active["filename"] = filename
                        if total_size > 0:
                            active["progress"] = (downloaded / total_size) * 100
                        
                        elapsed = time.time() - start_time
                        if elapsed > 1:
                            active["speed"] = downloaded / elapsed

        return file_path, filename
