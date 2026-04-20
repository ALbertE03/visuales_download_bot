import re
import requests
import time
import os
import asyncio
from functools import partial
from bot.config import CONFIG
from bot.utils import format_size, format_time
from bot.core.upload_worker import upload_file
from pyrogram import Client
from pyrogram.types import Message

def get_gdrive_id(url: str) -> str:
    """Extrae el ID de un enlace de Google Drive."""
    patterns = [
        r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/folderview\?id=([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_gdrive_file(file_id: str, destination: str, task_key: str):
    """Descarga un archivo de Google Drive usando requests."""
    URL = "https://docs.google.com/uc?export=download"
    
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
            
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    
    response.raise_for_status()
    
    content_disposition = response.headers.get('content-disposition')
    filename = "gdrive_file"
    if content_disposition:
        fname_match = re.findall('filename="(.+)"', content_disposition)
        if fname_match:
            filename = fname_match[0]
            
    if os.path.isdir(destination):
        file_path = os.path.join(destination, filename)
    else:
        file_path = destination
        filename = os.path.basename(file_path)

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    start_time = time.time()
    
    if task_key in CONFIG.status_data.value["active"]:
        CONFIG.status_data.value["active"][task_key]["filename"] = filename
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
    
    return file_path, filename

async def gdrive_handler(client: Client, message: Message) -> None:
    if len(message.command) < 2:
        await message.reply("Uso: /gdrive <url_de_google_drive>")
        return
    
    url = message.command[1]
    file_id = get_gdrive_id(url)
    
    if not file_id:
        await message.reply("Enlace de Google Drive no válido.")
        return
    
    status_msg = await message.reply("Analizando enlace de Google Drive...")
    
    task_key = f"dl_gdrive_{file_id[:10]}"
    CONFIG.status_data.value["active"][task_key] = {
        "filename": "Iniciando...",
        "progress": 0.0,
        "speed": 0.0,
        "downloaded": 0,
        "total": 0,
        "type": "download"
    }

    try:
        loop = asyncio.get_event_loop()
        file_path, filename = await loop.run_in_executor(
            None, 
            download_gdrive_file, 
            file_id, 
            CONFIG.DOWNLOAD_DIR.value,
            task_key
        )
        
        await status_msg.edit_text(f"Descarga de Google Drive completada: {filename}. Subiendo...")
        
        await upload_file(client, file_path, filename)
        
    except Exception as e:
        CONFIG.LOGGER.value.error(f"Error en gdrive_handler: {e}")
        await message.reply(f"Ocurrió un error: {str(e)}")
    finally:
        if task_key in CONFIG.status_data.value["active"]:
            del CONFIG.status_data.value["active"][task_key]
