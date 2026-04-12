import time
import os
import requests
import queue
import asyncio
from bot.config import CONFIG
from bot.core.upload_worker import upload_file
from pyrogram import Client


def download_file_worker(client: Client, loop: asyncio.AbstractEventLoop) -> None:
    """Procesador de la cola de descargas."""
    while True:
        while CONFIG.status_data.value.get("is_searching", False):
            time.sleep(1)
            
        try:
            item = CONFIG.download_queue.value.get(timeout=5)
            if item is None: break
            
            url, filename, retries = item
            file_path = os.path.join(CONFIG.DOWNLOAD_DIR.value, filename)
            task_key = f"dl_{filename}"
            
            CONFIG.status_data.value["active"][task_key] = {
                "filename": filename,
                "progress": 0.0,
                "speed": 0.0,
                "downloaded": 0,
                "total": 0,
                "type": "download"
            }
            
            CONFIG.LOGGER.value.info(f"Descargando {filename} desde {url}...")
            
            try:
                start_time = time.time()
                response = requests.get(url, stream=True, timeout=120)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                CONFIG.status_data.value["active"][task_key]["total"] = total_size
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192*1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if task_key in CONFIG.status_data.value["active"]:
                                CONFIG.status_data.value["active"][task_key]["downloaded"] = downloaded
                                if total_size > 0:
                                    CONFIG.status_data.value["active"][task_key]["progress"] = (downloaded / total_size) * 100
                                
                                elapsed = time.time() - start_time
                                if elapsed > 1:
                                    CONFIG.status_data.value["active"][task_key]["speed"] = downloaded / elapsed
                
                asyncio.run_coroutine_threadsafe(
                    upload_file(client, file_path, filename),
                    loop
                )
                
            except Exception as e:
                CONFIG.LOGGER.value.error(f"Error descargando {filename}: {e}")
                if retries < CONFIG.RETRY_MAX.value:
                    CONFIG.download_queue.value.put((url, filename, retries + 1))
                else:
                    CONFIG.status_data.value["failed"] += 1
            finally:
                if task_key in CONFIG.status_data.value["active"]:
                    del CONFIG.status_data.value["active"][task_key]
                
            CONFIG.status_data.value["total_in_queue"] = max(0, CONFIG.status_data.value["total_in_queue"] - 1)
            CONFIG.download_queue.value.task_done()
            
        except queue.Empty:
            continue
