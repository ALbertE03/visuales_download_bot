import re
import aiohttp
import os
from typing import Tuple
from bot.providers.base import BaseProvider
import urllib.parse
import time
from bot.config import CONFIG

class MediaFireProvider(BaseProvider):
    """Provider para descargar archivos de MediaFire."""

    def matches(self, url: str) -> bool:
        return "mediafire.com" in url

    async def get_direct_link(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                # Buscar el link directo en el HTML
                match = re.search(r'href="([^"]+)" id="downloadButton"', html)
                if match:
                    return match.group(1)
                raise Exception("No se pudo encontrar el enlace de descarga directo de MediaFire.")

    async def download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        direct_link = await self.get_direct_link(url)
        
        # Extraer nombre del archivo
        filename = urllib.parse.unquote(direct_link.split("/")[-1])
        file_path = os.path.join(destination, filename)

        async with aiohttp.ClientSession() as session:
            async with session.get(direct_link) as response:
                if response.status != 200:
                    raise Exception(f"Error HTTP {response.status} al descargar mediafire")
                
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                start_time = time.time()
                
                with open(file_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        if task_key not in CONFIG.status_data.value["active"]:
                            raise ValueError("Cancelado por el usuario")

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
