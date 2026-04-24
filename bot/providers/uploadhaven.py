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
        CONFIG.LOGGER.value.info(f"Usando UploadHavenProvider (curl) para: {url}")
        
        filename = "downloaded_file"
        import re
        from urllib.parse import unquote
        import subprocess

        filename_match = re.search(r"filename=([^&]+)", url)
        if filename_match:
            filename = unquote(filename_match.group(1))
        else:
            url_path = url.split("?")[0]
            filename = unquote(os.path.basename(url_path)) or "downloaded_file"

        file_path = os.path.join(destination, filename)
        
        # Primero obtenemos el tamaño del archivo con una petición HEAD (vía curl)
        try:
            head_cmd = [
                "curl", "-sI",
                "-L", # Seguir redirecciones
                "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "-e", "https://uploadhaven.com/",
                url
            ]
            head_output = subprocess.check_output(head_cmd, stderr=subprocess.STDOUT).decode('utf-8', errors='ignore')
            
            total_size = 0
            for line in head_output.splitlines():
                if line.lower().startswith("content-length:"):
                    total_size = int(line.split(":")[1].strip())
                    break
            
            CONFIG.status_data.value["active"][task_key]["total"] = total_size
        except Exception as e:
            CONFIG.LOGGER.value.warning(f"No se pudo obtener el tamaño del archivo con curl HEAD: {e}")
            total_size = 0

        # Comando curl para descargar
        curl_cmd = [
            "curl", "-L",
            "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "-e", "https://uploadhaven.com/",
            "-o", file_path,
            url
        ]
        
        # Iniciamos la descarga en un proceso separado
        process = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        start_time = time.time()
        while process.poll() is None:
            # Actualizamos el progreso basándonos en el tamaño del archivo en disco
            if os.path.exists(file_path):
                downloaded = os.path.getsize(file_path)
                if task_key in CONFIG.status_data.value["active"]:
                    CONFIG.status_data.value["active"][task_key]["downloaded"] = downloaded
                    if total_size > 0:
                        CONFIG.status_data.value["active"][task_key]["progress"] = (downloaded / total_size) * 100
                    
                    elapsed = time.time() - start_time
                    if elapsed > 1:
                        CONFIG.status_data.value["active"][task_key]["speed"] = downloaded / elapsed
            
            time.sleep(1)
            
        if process.returncode != 0:
            stderr = process.stderr.read().decode('utf-8', errors='ignore')
            raise Exception(f"Curl falló con código {process.returncode}: {stderr}")
            
        return file_path, filename
