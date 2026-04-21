import os
import time
import asyncio
import subprocess
from typing import Dict, List
from pyrogram import Client
from pyrogram.types import Message
from bot.config import CONFIG
from bot.core.upload_worker import upload_file
from bot.constants import CONSTANTS
from bot.utils import format_size

active_collections: Dict[int, List[Message]] = {}

async def add_handler(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    if chat_id in active_collections:
        await message.reply(CONSTANTS.MSG_COLLECTION_ALREADY_ACTIVE)
        return
        
    active_collections[chat_id] = []
    await message.reply(CONSTANTS.MSG_COLLECTION_STARTED)

async def end_handler(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    if chat_id not in active_collections:
        await message.reply(CONSTANTS.MSG_COLLECTION_NOT_ACTIVE)
        return
        
    messages = active_collections.pop(chat_id)
    if not messages:
        await message.reply(CONSTANTS.MSG_COLLECTION_EMPTY)
        return
        
    status_msg = await message.reply(CONSTANTS.MSG_COLLECTION_START_PACKING.format(count=len(messages)))
    
    asyncio.create_task(process_collection(client, message, messages, status_msg))


async def process_collection(client: Client, message: Message, messages: List[Message], status_msg: Message) -> None:
    chat_id = message.chat.id
    timestamp = int(time.time())
    work_dir = os.path.join(CONFIG.DOWNLOAD_DIR.value, f"recoleccion_{chat_id}_{timestamp}")
    os.makedirs(work_dir, exist_ok=True)
    
    downloaded_files = []
    
    total_files = len(messages)
    for idx, msg in enumerate(messages, start=1):
        try:
            prefix_text = CONSTANTS.MSG_COLLECTION_DOWNLOADING.format(idx=idx, total=total_files)
            
            last_edit_time = 0.0
            async def dl_progress(current: int, total: int):
                nonlocal last_edit_time
                now = time.time()
                if now - last_edit_time >= 2.0 or current == total:
                    last_edit_time = now
                    if total > 0:
                        percent = (current / total) * 100
                        filled = int(percent / 5)
                        bar = "█" * filled + "▒" * (20 - filled)
                        txt = f"{prefix_text}\n<code>[{bar}] {percent:.1f}%</code>\n<code>{format_size(current)}</code> de <code>{format_size(total)}</code>"
                    else:
                        txt = f"{prefix_text}\n<code>{format_size(current)}</code> descargados..."
                        
                    try:
                        await status_msg.edit_text(txt)
                    except Exception:
                        pass
                        
            await status_msg.edit_text(prefix_text)

            save_path = os.path.join(work_dir, f"{idx}_")
            file_path = await client.download_media(
                msg, 
                file_name=save_path,
                progress=dl_progress
            )
            if file_path:
                downloaded_files.append(file_path)
        except Exception as e:
            CONFIG.LOGGER.value.error(f"Error descargando el archivo {idx} de la recolección: {e}")
    
    if not downloaded_files:
        await status_msg.edit_text(CONSTANTS.MSG_COLLECTION_DOWNLOAD_ERROR)
        return
        
    await status_msg.edit_text(CONSTANTS.MSG_COLLECTION_COMPRESSING.format(count=len(downloaded_files)))
    
    target_zip = os.path.join(CONFIG.DOWNLOAD_DIR.value, f"Recoleccion_{timestamp}.zip")
    
    try:

        cmd = ["zip", "-9", "-j", target_zip] + downloaded_files
        #
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: subprocess.run(cmd, check=True))
    except Exception as e:
        CONFIG.LOGGER.value.error(f"Error comprimiendo zip de recolección: {e}")
        await status_msg.edit_text(CONSTANTS.MSG_COLLECTION_ZIP_ERROR)
        return
        
    await status_msg.edit_text(CONSTANTS.MSG_COLLECTION_UPLOAD_QUEUE)
    
    zip_filename = os.path.basename(target_zip)
    await upload_file(client, target_zip, zip_filename, chat_id)
    
    for f in downloaded_files:
        try:
            os.remove(f)
        except:
            pass
    try:
        os.rmdir(work_dir)
    except:
        pass

async def collection_monitor_handler(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    

    if chat_id not in active_collections:
        return

    if message.text and message.text.startswith('/'):
        return

    if message.document or message.audio or message.video:
        active_collections[chat_id].append(message)
        count = len(active_collections[chat_id])
        await message.reply(CONSTANTS.MSG_COLLECTION_FILE_ADDED.format(count=count), quote=True)
    else:
        del active_collections[chat_id]
        await message.reply(CONSTANTS.MSG_COLLECTION_CANCELLED, quote=True)
