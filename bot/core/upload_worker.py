import os 
import time
import asyncio
from bot.config import CONFIG
from bot.utils import format_size, save_processed
from pyrogram import Client
from typing import Optional



async def upload_file(client: Client, file_path: str, filename: str, destination_chat_id: Optional[int] = None) -> None:
    """Anade archivo a la cola de subida"""
    await CONFIG.upload_queue.value.put((file_path, filename, destination_chat_id))

async def upload_worker(client: Client) -> None:
    """Procesador de la cola de uploads."""
    while True:
        try:
            item = await CONFIG.upload_queue.value.get()
            if item is None: break
            
            file_path, filename, destination_chat_id = item
            target = destination_chat_id if destination_chat_id else CONFIG.TARGET_GROUP.value
            task_key = f"up_{filename}"
            
            try:
                if not os.path.exists(file_path):
                    CONFIG.LOGGER.value.error(f"Error: El archivo no existe: {file_path}")
                    CONFIG.status_data.value["failed"] += 1
                    CONFIG.upload_queue.value.task_done()
                    continue

                file_size = os.path.getsize(file_path)
                CONFIG.LOGGER.value.info(f"Subiendo {filename} ({format_size(file_size)}) a {target}...")
                
                CONFIG.status_data.value["active"][task_key] = {
                    "filename": filename,
                    "progress": 0.0,
                    "speed": 0.0,
                    "downloaded": 0,
                    "total": file_size,
                    "type": "upload"
                }
                
                start_time = time.time()

                async def progress_callback(current: int, total: int) -> None:
                    if task_key not in CONFIG.status_data.value["active"]:
                        return
                    
                    elapsed = time.time() - start_time
                    CONFIG.status_data.value["active"][task_key]["downloaded"] = current
                    CONFIG.status_data.value["active"][task_key]["total"] = total
                    
                    if total > 0:
                        CONFIG.status_data.value["active"][task_key]["progress"] = (current / total) * 100
                    
                    if elapsed > 0.1:
                        CONFIG.status_data.value["active"][task_key]["speed"] = current / elapsed
                    else:
                        CONFIG.status_data.value["active"][task_key]["speed"] = 0.0

                for try_count in range(CONFIG.RETRY_MAX.value + 1):
                    try:
                        await client.send_document(
                            chat_id=target,
                            document=file_path,
                            file_name=filename,
                            caption=f"{filename}",
                            progress=progress_callback
                        )
                        CONFIG.LOGGER.value.info(f"Finalizado: {filename} enviado con exito.")
                        break
                    except Exception as e:
                        if "call_exception_handler" in str(e) or "NoneType" in str(e):
                            CONFIG.LOGGER.value.warning(f"Error de sesion detectado en {filename}, esperando para reintentar...")
                            await asyncio.sleep(10)
                        
                        if try_count < CONFIG.RETRY_MAX.value:
                            CONFIG.LOGGER.value.warning(f"Error subiendo {filename} (intento {try_count + 1}): {e}. Reintentando...")
                            await asyncio.sleep(5)
                        else:
                            raise e
                
                CONFIG.status_data.value["completed"] += 1
                save_processed(filename)

                if os.path.exists(file_path):
                    os.remove(file_path)
                    CONFIG.LOGGER.value.info(f"Archivo local eliminado: {filename}")
                    
            except Exception as e:
                CONFIG.LOGGER.value.error(f"Error subiendo {filename}: {e}")
                CONFIG.status_data.value["failed"] += 1
            finally:
                if task_key in CONFIG.status_data.value["active"]:
                    del CONFIG.status_data.value["active"][task_key]
                CONFIG.upload_queue.value.task_done()
                
        except Exception as e:
            print(f"Error en worker de subida: {e}")
            await asyncio.sleep(1)
