import os
import subprocess
import time
import asyncio
import re
from typing import Tuple
from urllib.parse import unquote
from bot.providers.base import BaseProvider
from bot.config import CONFIG

class UploadHavenProvider(BaseProvider):
    def matches(self, url: str) -> bool:
        return "uploadhaven.com" in url.lower()

    async def download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_download, url, destination, task_key)

    def _sync_download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        CONFIG.LOGGER.value.info(f"Descargando con curl directo: {url}")
        
        # Extraer nombre del archivo
        filename = "file.zip"
        filename_match = re.search(r"filename=([^&]+)", url)
        if filename_match:
            filename = unquote(filename_match.group(1))
        else:
            url_path = url.split("?")[0]
            filename = unquote(os.path.basename(url_path)) or "file.zip"
        
        file_path = os.path.join(destination, filename)
        
        # Comando curl directo (como en terminal)
        # Usamos -L para seguir redirecciones si las hay
        cmd = ["curl", "-L", url, "--output", file_path]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        start_time = time.time()
        while process.poll() is None:
            if os.path.exists(file_path):
                downloaded = os.path.getsize(file_path)
                if task_key in CONFIG.status_data.value["active"]:
                    active = CONFIG.status_data.value["active"][task_key]
                    active["downloaded"] = downloaded
                    # Si ya tenemos el total de la respuesta anterior o algo, lo usamos
                    # pero curl --output no nos da el total fácilmente sin parsear stderr
                    elapsed = time.time() - start_time
                    if elapsed > 1:
                        active["speed"] = downloaded / elapsed
            time.sleep(2)
            
        if process.returncode != 0:
            stderr = process.stderr.read().decode("utf-8", errors="ignore")
            raise Exception(f"Curl falló: {stderr}")
            
        return file_path, filename
