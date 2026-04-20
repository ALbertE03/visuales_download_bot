import asyncio
import time
import os
from functools import partial
import yt_dlp
from bot.config import CONFIG
from bot.utils import format_size, format_time
from bot.core.upload_worker import upload_file
from pyrogram import Client
from pyrogram.types import Message

async def twitter_handler(client: Client, message: Message) -> None:
    """Manejador para descargar videos de Twitter (X) usando yt-dlp."""
    if len(message.command) < 2:
        await message.reply("Uso: /twitter <url_de_twitter>")
        return
    
    url = message.command[1]
    status_msg = await message.reply("Analizando enlace de Twitter...")
    
    ydl_opts = {
        "format": "best",
        "outtmpl": f"{CONFIG.DOWNLOAD_DIR.value}/twitter_%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
         "noprogress": False
    }

    try:
        loop = asyncio.get_event_loop()
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(
                None, 
                partial(ydl.extract_info, url, download=False)
            )
            
            title = info.get('title', 'twitter_video')
            task_key = f"dl_tw_{info.get('id', int(time.time()))}"
            
            CONFIG.status_data.value["active"][task_key] = {
                "filename": title,
                "progress": 0.0,
                "speed": 0.0,
                "downloaded": 0,
                "total": 0,
                "type": "download"
            }

            def progress_hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes', 0)
                    speed = d.get('speed', 0) or 0
                    
                    if task_key in CONFIG.status_data.value["active"]:
                        CONFIG.status_data.value["active"][task_key]["downloaded"] = downloaded
                        if total > 0:
                            CONFIG.status_data.value["active"][task_key]["progress"] = (downloaded / total) * 100
                        CONFIG.status_data.value["active"][task_key]["speed"] = speed

            ydl.add_progress_hook(progress_hook)
            await status_msg.edit_text(f"Descargando de Twitter: {title}...")
            
            await loop.run_in_executor(None, partial(ydl.download, [url]))
            
            filename = ydl.prepare_filename(info)
            await status_msg.edit_text(f"Descarga de Twitter completada. Subiendo...")
            await upload_file(client, filename, os.path.basename(filename))
            
    except Exception as e:
        CONFIG.LOGGER.value.error(f"Error en twitter_handler: {e}")
        await message.reply(f"Error al descargar de Twitter: {str(e)}")
    finally:
        if 'task_key' in locals() and task_key in CONFIG.status_data.value["active"]:
            del CONFIG.status_data.value["active"][task_key]
