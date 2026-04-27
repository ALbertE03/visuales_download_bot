import yt_dlp
import asyncio
import os
from typing import Tuple
from bot.providers.base import BaseProvider
from bot.config import CONFIG
from bot.constants import CONSTANTS

class YoutubeDLProvider(BaseProvider):
    def matches(self, url: str) -> bool:
        return any(x in url.lower() for x in CONSTANTS.YDL_SUPPORTED_DOMAINS)

    async def download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        loop = asyncio.get_event_loop()
        
        ydl_opts = CONSTANTS.YDL_OPTS_DEFAULT.copy()
        ydl_opts["outtmpl"] = f"{destination}/%(title)s.%(ext)s"

        def progress_hook(d):
            if task_key not in CONFIG.status_data.value["active"]:
                raise ValueError("Cancelado por el usuario")

            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0) or 0
                
                if task_key in CONFIG.status_data.value["active"]:
                    active = CONFIG.status_data.value["active"][task_key]
                    active["progress"] = (downloaded / total * 100) if total > 0 else 0
                    active["speed"] = speed
                    active["downloaded"] = downloaded
                    active["total"] = total
                    active["filename"] = d.get('filename', 'Video').split('/')[-1]

        ydl_opts["progress_hooks"] = [progress_hook]

        def extract_and_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename, os.path.basename(filename)

        return await loop.run_in_executor(None, extract_and_download)
