import time
import os
import requests
import queue
import asyncio
from bot.config import (
    status_data, download_queue, DOWNLOAD_DIR, 
    RETRY_MAX
)
from bot.core.upload_worker import upload_file
from pyrogram import Client


def download_file_worker(client: Client, loop: asyncio.AbstractEventLoop) -> None:
    """Procesador de la cola de descargas."""
    while True:
        while status_data.get("is_searching", False):
            time.sleep(1)
            
        try:
            item = download_queue.get(timeout=5)
            if item is None: break
            
            url, filename, retries = item
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            task_key = f"dl_{filename}"
            
            status_data["active"][task_key] = {
                "filename": filename,
                "progress": 0.0,
                "speed": 0.0,
                "downloaded": 0,
                "total": 0,
                "type": "download"
            }
            
            print(f"Descargando {filename} desde {url}...")
            
            try:
                start_time = time.time()
                response = requests.get(url, stream=True, timeout=120)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                status_data["active"][task_key]["total"] = total_size
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192*1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if task_key in status_data["active"]:
                                status_data["active"][task_key]["downloaded"] = downloaded
                                if total_size > 0:
                                    status_data["active"][task_key]["progress"] = (downloaded / total_size) * 100
                                
                                elapsed = time.time() - start_time
                                if elapsed > 1:
                                    status_data["active"][task_key]["speed"] = downloaded / elapsed
                
                asyncio.run_coroutine_threadsafe(
                    upload_file(client, file_path, filename),
                    loop
                )
                
            except Exception as e:
                print(f"Error descargando {filename}: {e}")
                if retries < RETRY_MAX:
                    download_queue.put((url, filename, retries + 1))
                else:
                    status_data["failed"] += 1
            finally:
                if task_key in status_data["active"]:
                    del status_data["active"][task_key]
                
            status_data["total_in_queue"] = max(0, status_data["total_in_queue"] - 1)
            download_queue.task_done()
            
        except queue.Empty:
            continue
