import time
import os
import requests
import queue
import asyncio
from bot.config import CONFIG
from bot.core.upload_worker import upload_file
from bot.constants import CONSTANTS
from pyrogram import Client
from bot.manager import manager


def download_file_worker(client: Client, loop: asyncio.AbstractEventLoop) -> None:
    """Procesador de la cola de descargas."""
    while True:
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
                "type": CONSTANTS.TASK_TYPE_DOWNLOAD
            }
            
            CONFIG.LOGGER.value.info(CONSTANTS.LOG_DOWNLOADING.format(filename=filename, url=url))
            
            try:
                start_time = time.time()
                
                provider = manager.get_provider(url)
                if provider:
                    future = asyncio.run_coroutine_threadsafe(
                        provider.download(url, CONFIG.DOWNLOAD_DIR.value, task_key),
                        loop
                    )
                    file_path, filename = future.result()
                else:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    response = requests.get(url, stream=True, timeout=120, headers=headers)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    CONFIG.status_data.value["active"][task_key]["total"] = total_size
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=CONSTANTS.CHUNK_SIZE):
                            if chunk:
                                if task_key not in CONFIG.status_data.value["active"]:
                                    raise asyncio.CancelledError("Cancelado por el usuario")
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if task_key in CONFIG.status_data.value["active"]:
                                    CONFIG.status_data.value["active"][task_key]["downloaded"] = downloaded
                                    if total_size > 0:
                                        CONFIG.status_data.value["active"][task_key]["progress"] = (downloaded / total_size) * 100
                                    
                                    elapsed = time.time() - start_time
                                    if elapsed > 1:
                                        CONFIG.status_data.value["active"][task_key]["speed"] = downloaded / elapsed
                
                if task_key in CONFIG.status_data.value["active"]:
                    asyncio.run_coroutine_threadsafe(
                        upload_file(client, file_path, filename),
                        loop
                    )
                
            except Exception as e:
                if "Cancelado" in str(e):
                    CONFIG.LOGGER.value.info(f"Tarea {filename} cancelada por el usuario.")
                    CONFIG.status_data.value["failed"] += 1
                else:
                    CONFIG.LOGGER.value.error(CONSTANTS.LOG_ERROR_DOWNLOADING.format(filename=filename, error=e))
                    if retries < CONFIG.RETRY_MAX.value:
                        CONFIG.download_queue.value.put((url, filename, retries + 1))
                    else:
                        CONFIG.status_data.value["failed"] += 1
                
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
            finally:
                if task_key in CONFIG.status_data.value["active"]:
                    del CONFIG.status_data.value["active"][task_key]
                
            CONFIG.status_data.value["total_in_queue"] = max(0, CONFIG.status_data.value["total_in_queue"] - 1)
            CONFIG.download_queue.value.task_done()
            
        except queue.Empty:
            continue
