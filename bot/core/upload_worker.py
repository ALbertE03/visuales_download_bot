import os 
import time
import asyncio
from bot.config import CONFIG
from bot.utils import format_size, save_processed,split_file
from bot.constants import CONSTANTS
from pyrogram import Client
from typing import Optional



async def upload_file(client: Client, file_path: str, filename: str, destination_chat_id: Optional[int] = None) -> None:
    """Anade archivo a la cola de subida. Si es muy grande, lo divide primero."""
    if os.path.isdir(file_path):
        CONFIG.LOGGER.value.info(CONSTANTS.LOG_DETECTED_DIR.format(filename=filename))
        for root, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(root, file)
                await upload_file(client, full_path, file, destination_chat_id)
        return

    if os.path.isfile(file_path):
        file_size = os.path.getsize(file_path)
        if file_size > 2000 * 1024 * 1024:  # > 2GB
            CONFIG.LOGGER.value.info(CONSTANTS.LOG_SPLITTING.format(filename=filename))
            
            task_key = f"split_{filename}"
            CONFIG.status_data.value["active"][task_key] = {
                "filename": filename,
                "progress": 0.0,
                "speed": 0.0,
                "downloaded": 0,
                "total": file_size,
                "type": "split"
            }
            
            loop = asyncio.get_event_loop()
            
            async def monitor_split_progress():
                dir_path = os.path.dirname(file_path)
                base_filename = os.path.basename(file_path)
                last_size = 0
                last_time = time.time()
                
                while task_key in CONFIG.status_data.value["active"]:
                    try:
                        current_size = sum(
                            os.path.getsize(os.path.join(dir_path, f)) 
                            for f in os.listdir(dir_path) 
                            if f.startswith(base_filename) and (f.endswith(".zip") or ".z" in f)
                        )
                        active = CONFIG.status_data.value["active"][task_key]
                        active["downloaded"] = current_size
                        
                        now = time.time()
                        elapsed = now - last_time
                        if elapsed >= 1:
                            active["speed"] = (current_size - last_size) / elapsed
                            last_size = current_size
                            last_time = now
                            
                        if active["total"] > 0:
                            active["progress"] = min(100.0, (current_size / active["total"]) * 100)
                    except Exception:
                        pass
                    await asyncio.sleep(2)
                    
            monitor_task = asyncio.create_task(monitor_split_progress())
            
            try:
                parts = await loop.run_in_executor(None, split_file, file_path, 1000) 
            finally:
                if task_key in CONFIG.status_data.value["active"]:
                    del CONFIG.status_data.value["active"][task_key]
                monitor_task.cancel()
                
            for part in parts:
                await CONFIG.upload_queue.value.put((part, os.path.basename(part), destination_chat_id))
            try:
                os.remove(file_path)
            except:
                pass
            return

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
                    CONFIG.LOGGER.value.error(CONSTANTS.ERR_FILE_NOT_FOUND.format(path=file_path))
                    CONFIG.status_data.value["failed"] += 1
                    CONFIG.upload_queue.value.task_done()
                    continue

                file_size = os.path.getsize(file_path)
                CONFIG.LOGGER.value.info(CONSTANTS.LOG_UPLOADING.format(filename=filename, size=format_size(file_size), target=target))
                
                CONFIG.status_data.value["active"][task_key] = {
                    "filename": filename,
                    "progress": 0.0,
                    "speed": 0.0,
                    "downloaded": 0,
                    "total": file_size,
                    "type": CONSTANTS.TASK_TYPE_UPLOAD
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
                        CONFIG.LOGGER.value.info(CONSTANTS.LOG_UPLOAD_SUCCESS.format(filename=filename))
                        break
                    except Exception as e:
                        if "call_exception_handler" in str(e) or "NoneType" in str(e):
                            CONFIG.LOGGER.value.warning(CONSTANTS.LOG_SESSION_ERROR.format(filename=filename))
                            await asyncio.sleep(10)
                        
                        if try_count < CONFIG.RETRY_MAX.value:
                            CONFIG.LOGGER.value.warning(CONSTANTS.LOG_UPLOAD_RETRY.format(filename=filename, attempt=try_count + 1, error=e))
                            await asyncio.sleep(5)
                        else:
                            raise e
                
                CONFIG.status_data.value["completed"] += 1
                save_processed(filename)

                if os.path.exists(file_path):
                    os.remove(file_path)
                    CONFIG.LOGGER.value.info(CONSTANTS.LOG_FILE_DELETED.format(filename=filename))
                    
            except Exception as e:
                CONFIG.LOGGER.value.error(CONSTANTS.LOG_UPLOAD_ERROR.format(filename=filename, error=e))
                CONFIG.status_data.value["failed"] += 1
            finally:
                if task_key in CONFIG.status_data.value["active"]:
                    del CONFIG.status_data.value["active"][task_key]
                CONFIG.upload_queue.value.task_done()
                
        except Exception as e:
            CONFIG.LOGGER.value.error(CONSTANTS.LOG_UPLOAD_WORKER_ERROR.format(error=e))
            await asyncio.sleep(1)
