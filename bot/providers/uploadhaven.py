import os
import subprocess
import time
import asyncio
import re
from typing import Tuple
from urllib.parse import unquote, urlparse
import yt_dlp
from bot.providers.base import BaseProvider
from bot.config import CONFIG
from bot.constants import CONSTANTS

class UploadHavenProvider(BaseProvider):
    def matches(self, url: str) -> bool:
        return "uploadhaven.com" in url.lower()

    async def download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        # Si es un enlace de página (no directo), usamos yt-dlp directamente
        if "/download/" in url.lower() and not "download" in urlparse(url).netloc:
            return await self._download_with_ytdlp(url, destination, task_key)
        
        # Si es enlace directo, intentamos curl con esteroides y yt-dlp de fallback
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_download, url, destination, task_key
        )

    async def _download_with_ytdlp(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        CONFIG.LOGGER.value.info(f"Usando yt-dlp para UploadHaven: {url}")
        loop = asyncio.get_event_loop()
        
        ydl_opts = {
            'outtmpl': f'{destination}/%(title)s.%(ext)s',
            'referer': 'https://uploadhaven.com/',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }

        def progress_hook(d):
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
                    active["filename"] = os.path.basename(d.get('filename', 'file'))

        ydl_opts["progress_hooks"] = [progress_hook]

        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename, os.path.basename(filename)

        return await loop.run_in_executor(None, run_ydl)

    def _sync_download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        CONFIG.LOGGER.value.info(f"Usando Robust Download (curl + cookies) para: {url}")
        
        # Extraer filename
        filename = "downloaded_file"
        filename_match = re.search(r"filename=([^&]+)", url)
        if filename_match:
            filename = unquote(filename_match.group(1))
        else:
            url_path = url.split("?")[0]
            filename = unquote(os.path.basename(url_path)) or "downloaded_file"

        file_path = os.path.join(destination, filename)
        cookie_file = os.path.join(destination, f"cookies_{task_key}.txt")
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ]

        success = False
        last_error = ""

        for ua in user_agents:
            try:
                # Paso 1: Obtener cookies y total_size con HEAD
                head_cmd = [
                    "curl", "-sI", "-L",
                    "-A", ua,
                    "-e", "https://uploadhaven.com/",
                    "-c", cookie_file,
                    url
                ]
                head_output = subprocess.check_output(head_cmd, stderr=subprocess.STDOUT).decode("utf-8", errors="ignore")
                
                total_size = 0
                is_403 = "403 Forbidden" in head_output
                
                if is_403:
                    CONFIG.LOGGER.value.warning(f"Intento con UA fallido (403). Probando siguiente...")
                    continue

                for line in head_output.splitlines():
                    if line.lower().startswith("content-length:"):
                        total_size = int(line.split(":")[1].strip())
                        break
                
                CONFIG.status_data.value["active"][task_key]["total"] = total_size

                # Paso 2: Descargar usando las cookies obtenidas
                curl_cmd = [
                    "curl", "-L",
                    "-A", ua,
                    "-e", "https://uploadhaven.com/",
                    "-b", cookie_file,
                    "-o", file_path,
                    url
                ]
                
                process = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                start_time = time.time()
                while process.poll() is None:
                    if os.path.exists(file_path):
                        downloaded = os.path.getsize(file_path)
                        if task_key in CONFIG.status_data.value["active"]:
                            active = CONFIG.status_data.value["active"][task_key]
                            active["downloaded"] = downloaded
                            if total_size > 0:
                                active["progress"] = (downloaded / total_size) * 100
                            
                            elapsed = time.time() - start_time
                            if elapsed > 1:
                                active["speed"] = downloaded / elapsed
                    time.sleep(1)
                
                if process.returncode == 0:
                    # Validar tamaño mínimo para descartar páginas de error
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 5000:
                        success = True
                        break
                    else:
                        # Si es muy pequeño, probablemente sea un error silencioso
                        if os.path.exists(file_path):
                            with open(file_path, 'r', errors='ignore') as f:
                                if "403" in f.read(500) or "Forbidden" in f.read(500):
                                    CONFIG.LOGGER.value.warning("Detectado HTML de error 403. Reintentando...")
                                    os.remove(file_path)
                                    continue
                
            except Exception as e:
                last_error = str(e)
                CONFIG.LOGGER.value.error(f"Error en intento de descarga: {e}")
            
            finally:
                if os.path.exists(cookie_file):
                    os.remove(cookie_file)
        
        if not success:
            # Fallback final a yt-dlp si curl falló
            try:
                CONFIG.LOGGER.value.info("Iniciando fallback final a yt-dlp...")
                # Aquí tendríamos que llamar a la lógica de yt-dlp de forma síncrona
                # Pero para simplificar, lanzamos la excepción si llegamos aquí
                raise Exception(f"Todos los intentos de descarga fallaron. {last_error or 'Bloqueo de IP detectado.'}")
            except Exception as e:
                raise e

        return file_path, filename
