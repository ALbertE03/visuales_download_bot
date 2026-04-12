import time
import os
import requests
import queue
import asyncio
from bot.config import (
    status_data, download_queue, DOWNLOAD_DIR, 
    RETRY_MAX
)
from bot.utils import format_size, format_time
from pyrogram import Client
from typing import Optional


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

async def update_status_message(client: Client) -> None:
    """Actualiza el mensaje de estado en Telegram."""
    last_text = ""
    while True:
        try:
            if status_data["status_message"]:
                lines = ["[ PANEL DE CONTROL ]\n"]
                active_list = list(status_data["active"].values())
                
                if not active_list:
                    if status_data["total_in_queue"] > 0:
                        lines.append("Esperando para iniciar tareas...")
                    else:
                        lines.append("Sin tareas activas en este momento.")
                else:
                    for data in active_list:
                        speed = data.get("speed", 0)
                        speed_fmt = format_size(speed) + "/s"
                        downloaded_fmt = format_size(data.get("downloaded", 0))
                        total = data.get("total", 0)
                        total_fmt = format_size(total)
                        progress = data.get("progress", 0.0)
                        
                        filled = int(progress / 10)
                        bar = "▰" * filled + "▱" * (10 - filled)
                        
                        task_type = "DESCARGANDO" if data.get("type") == "download" else "SUBIENDO"
                        lines.append(f"== {task_type} ==")
                        lines.append(f"Archivo: {data['filename']}")
                        lines.append(f"[{bar}] {progress:.1f}%")
                        
                        eta_val = "calculando..."
                        if speed > 0 and total > 0:
                            remaining = total - data.get("downloaded", 0)
                            eta_val = format_time(remaining / speed)
                        
                        lines.append(f"{downloaded_fmt} de {total_fmt}")
                        lines.append(f"Velocidad: {speed_fmt}")
                        lines.append(f"Restante: {eta_val}\n")
                
                lines.append("⎯" * 15)
                lines.append(f"Completados: {status_data['completed']}")
                lines.append(f"Fallidos: {status_data['failed']}")
                lines.append(f"En Cola: {status_data['total_in_queue']}")
                
                txt = "\n".join(lines)
                
                if txt != last_text:
                    try:
                        await status_data["status_message"].edit_text(txt)
                        last_text = txt
                    except Exception as e:
                        if "MESSAGE_ID_INVALID" in str(e) or "MESSAGE_NOT_MODIFIED" not in str(e):
                            pass
            
            await asyncio.sleep(4)
        except Exception as e:
            print(f"Error en bucle de status: {e}")
            await asyncio.sleep(5)
