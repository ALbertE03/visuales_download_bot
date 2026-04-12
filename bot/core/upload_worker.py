import os 
import time
import os
import asyncio
from bot.config import (
    status_data, upload_queue, 
    RETRY_MAX, TARGET_GROUP
)
from bot.utils import format_size, save_processed
from pyrogram import Client
from typing import Optional



async def upload_file(client: Client, file_path: str, filename: str, destination_chat_id: Optional[int] = None) -> None:
    """Anade archivo a la cola de subida"""
    await upload_queue.put((file_path, filename, destination_chat_id))

async def upload_worker(client: Client) -> None:
    """Procesador de la cola de uploads."""
    while True:
        try:
            item = await upload_queue.get()
            if item is None: break
            
            file_path, filename, destination_chat_id = item
            target = destination_chat_id if destination_chat_id else TARGET_GROUP
            task_key = f"up_{filename}"
            
            try:
                if not os.path.exists(file_path):
                    print(f"Error: El archivo no existe: {file_path}")
                    status_data["failed"] += 1
                    upload_queue.task_done()
                    continue

                file_size = os.path.getsize(file_path)
                print(f"Subiendo {filename} ({format_size(file_size)}) a {target}...")
                
                status_data["active"][task_key] = {
                    "filename": filename,
                    "progress": 0.0,
                    "speed": 0.0,
                    "downloaded": 0,
                    "total": file_size,
                    "type": "upload"
                }
                
                start_time = time.time()

                async def progress_callback(current: int, total: int) -> None:
                    if task_key not in status_data["active"]:
                        return
                    
                    elapsed = time.time() - start_time
                    status_data["active"][task_key]["downloaded"] = current
                    status_data["active"][task_key]["total"] = total
                    
                    if total > 0:
                        status_data["active"][task_key]["progress"] = (current / total) * 100
                    
                    if elapsed > 0.1:
                        status_data["active"][task_key]["speed"] = current / elapsed
                    else:
                        status_data["active"][task_key]["speed"] = 0.0

                for try_count in range(RETRY_MAX + 1):
                    try:
                        await client.send_document(
                            chat_id=target,
                            document=file_path,
                            file_name=filename,
                            caption=f"{filename}",
                            progress=progress_callback
                        )
                        print(f"Finalizado: {filename} enviado con exito.")
                        break
                    except Exception as e:
                        if try_count < RETRY_MAX:
                            print(f"Error subiendo {filename} (intento {try_count + 1}): {e}. Reintentando...")
                            await asyncio.sleep(5)
                        else:
                            raise e
                
                status_data["completed"] += 1
                save_processed(filename)

                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Archivo local eliminado: {filename}")
                    
            except Exception as e:
                print(f"Error subiendo {filename}: {e}")
                status_data["failed"] += 1
            finally:
                if task_key in status_data["active"]:
                    del status_data["active"][task_key]
                upload_queue.task_done()
                
        except Exception as e:
            print(f"Error en worker de subida: {e}")
            await asyncio.sleep(1)
