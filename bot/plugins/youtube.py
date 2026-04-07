import time
import os
import asyncio
import yt_dlp
from functools import partial
from bot.config import status_data, DOWNLOAD_DIR
from bot.utils import format_size, format_time
from bot.core.workers import upload_file
from pyrogram import Client
from pyrogram.types import Message


async def yt_handler(client: Client, message: Message) -> None:
    print(f"[DEBUG] Comando /yt recibido: {message.text}")
    if len(message.command) < 2:
        await message.reply("Uso: /yt <url> [720, 1080, etc]")
        return
    
    chat_id = message.chat.id
    url = message.command[1]
    quality = "best"
    
    if len(message.command) >= 3:
        for arg in message.command[2:]:
            if arg.isdigit():
                quality = f"bestvideo[height<={arg}]+bestaudio/best[height<={arg}]"


    status_msg = await message.reply("Analizando video...")

    ydl_opts = {
        "format": quality,
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
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
            
            title = info.get('title', 'video')
            duration = format_time(info.get('duration'))
            uploader = info.get('uploader', 'Desconocido')
            views = info.get('view_count', 0)
            actual_res = f"{info.get('height', 'Desc')}p" if info.get('height') else "Best"
            
            metadata_text = (
                f"[ INFO DEL VIDEO ]\n"
                f"Titulo: {title}\n"
                f"Calidad: {actual_res}\n"
                f"Canal: {uploader}\n"
                f"Duracion: {duration}\n"
                f"Vistas: {views:,}\n\n"
                f"Descargando..."
            )
            await status_msg.edit_text(metadata_text)
            
            task_key = f"dl_yt_{title[:20]}"
            last_edit_time = 0

            def progress_hook(d):
                nonlocal last_edit_time
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes', 0)
                    
                    if total > 0:
                        progress = (downloaded / total) * 100
                    else:
                        progress = 0.0
                    
                    speed = d.get('speed', 0) or 0
                    
                    status_data["active"][task_key] = {
                        "filename": title,
                        "progress": progress,
                        "speed": speed,
                        "downloaded": downloaded,
                        "total": total,
                        "type": "download"
                    }

                    current_time = time.time()
                    if current_time - last_edit_time > 5: 
                        filled = int(progress / 10)
                        bar = "▰" * filled + "▱" * (10 - filled)
                        speed_fmt = format_size(speed) + "/s"
                        
                        msg_text = (
                            f"[ DESCARGA YOUTUBE ]\n"
                            f"Archivo: {title}\n"
                            f"Calidad: {actual_res}\n"
                            f"[{bar}] {progress:.1f}%\n"
                            f"{format_size(downloaded)} de {format_size(total)} | {speed_fmt}"
                        )
                        
                        async def edit_msg():
                            try:
                                await status_msg.edit_text(msg_text)
                            except:
                                pass

                        asyncio.run_coroutine_threadsafe(
                            edit_msg(),
                            loop
                        )
                        last_edit_time = current_time

                elif d['status'] == 'finished':
                    if task_key in status_data["active"]:
                        del status_data["active"][task_key]

            ydl.add_progress_hook(progress_hook)
            await loop.run_in_executor(None, partial(ydl.download, [url]))
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            base = filename.rsplit('.', 1)[0]
            found = False
            for ext in ['.mp4', '.webm', '.mkv']:
                if os.path.exists(base + ext):
                    filename = base + ext
                    found = True
                    break
            if not found:
                await status_msg.edit_text("Error: No se encontro el archivo descargado")
                return
        
        real_filename = os.path.basename(filename)
        print(f"[DEBUG] Archivo listo para subir: {filename}")
        await status_msg.edit_text(f"Preparando envio del archivo: {real_filename}")
        await upload_file(client, filename, real_filename, destination_chat_id=chat_id)
        
    except yt_dlp.utils.DownloadError as e:
        await status_msg.edit_text(f"Error de descarga: No se pudo procesar el video. Verifique la URL o la calidad solicitada.")
    except Exception as e:
        await status_msg.edit_text(f"Error inesperado: {str(e)}")
        print(f"Error en yt: {e}")
