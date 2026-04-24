import os
import requests
import time
import asyncio
from typing import Tuple
from bot.providers.base import BaseProvider
from bot.config import CONFIG
from bot.constants import CONSTANTS
import re
from urllib.parse import unquote


class UploadHavenProvider(BaseProvider):
    def matches(self, url: str) -> bool:
        return "uploadhaven.com" in url.lower()

    async def download(
        self, url: str, destination: str, task_key: str
    ) -> Tuple[str, str]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_download, url, destination, task_key
        )

    def _sync_download(
        self, url: str, destination: str, task_key: str
    ) -> Tuple[str, str]:
        CONFIG.LOGGER.value.info(f"Usando UploadHavenProvider para: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://uploadhaven.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
        }

        filename = "downloaded_file"

        filename_match = re.search(r"filename=([^&]+)", url)
        if filename_match:
            filename = unquote(filename_match.group(1))
        else:
            url_path = url.split("?")[0]
            filename = unquote(os.path.basename(url_path)) or "downloaded_file"

        file_path = os.path.join(destination, filename)

        response = requests.get(url, stream=True, timeout=120, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        CONFIG.status_data.value["active"][task_key]["total"] = total_size

        start_time = time.time()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=CONSTANTS.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if task_key in CONFIG.status_data.value["active"]:
                        CONFIG.status_data.value["active"][task_key][
                            "downloaded"
                        ] = downloaded
                        if total_size > 0:
                            CONFIG.status_data.value["active"][task_key]["progress"] = (
                                downloaded / total_size
                            ) * 100

                        elapsed = time.time() - start_time
                        if elapsed > 1:
                            CONFIG.status_data.value["active"][task_key]["speed"] = (
                                downloaded / elapsed
                            )

        return file_path, filename
