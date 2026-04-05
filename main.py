
import os
import requests
import threading
import queue
import time
import math
import asyncio
import json
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
from functools import partial

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_GROUP = os.getenv("TARGET_GROUP")
BASE_URL = os.getenv("BASE_URL", "https://visuales.uclv.cu/")
CANT_WORKER=3
UPLOAD_WORKER=3
DOWNLOAD_DIR = "downloads"
PROCESSED_DB = "processed.json"
FORMATS = ('.mp4', '.mkv', '.avi', '.mpg', '.dat', '.wmv', '.mov', '.mpg', '.mpeg')


os.makedirs(DOWNLOAD_DIR,exist_ok=True)



def load_processed():
    if os.path.exists(PROCESSED_DB):
        try:
            with open(PROCESSED_DB, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def save_processed(filename):
    data = list(load_processed())
    if filename not in data:
        data.append(filename)
        with open(PROCESSED_DB, "w") as f: json.dump(data, f)

download_queue = queue.Queue()
upload_queue = asyncio.Queue()
retry_max = 3

status_data = {
    "active": {}, # {thread_id: {filename, progress, speed, downloaded, total, type}}
    "completed": 0,
    "failed": 0,
    "total_in_queue": 0,
    "is_searching": False,  
    "status_message": None  
}

def format_size(size_bytes):
    if size_bytes <= 0: return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def format_time(seconds):
    if seconds is None or seconds < 0: return "Desconocido"
    if seconds == float('inf'): return "Desconocido"
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def upload_worker(client):
    """Procesador de la cola de uploads."""
    while True:
        try:
            item = await upload_queue.get()
            if item is None: break
            
            file_path, filename = item
            
            task_key = f"up_{filename}"
            try:
                print(f"Subiendo {filename} a Telegram...")
                
                file_size = os.path.getsize(file_path)
                status_data["active"][task_key] = {
                    "filename": filename,
                    "progress": 0.0,
                    "speed": 0.0,
                    "downloaded": 0,
                    "total": file_size,
                    "type": "upload"
                }
                
                start_time = time.time()

                async def progress_callback(current, total):
                    if task_key not in status_data["active"]:
                        return

                    elapsed = time.time() - start_time
                    status_data["active"][task_key]["downloaded"] = current
                    status_data["active"][task_key]["total"] = total
                    if total > 0:
                        status_data["active"][task_key]["progress"] = (current / total) * 100
                    if elapsed > 1:
                        status_data["active"][task_key]["speed"] = current / elapsed

                await client.send_document(
                    chat_id=TARGET_GROUP,
                    document=file_path,
                    file_name=filename,
                    caption=f"**{filename}**",
                    progress=progress_callback
                )
                print(f"Finalizado: {filename} enviado.")
                
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

async def upload_file(client, file_path, filename):
    """Añade archivo a la cola de subida"""
    await upload_queue.put((file_path, filename))

async def update_status_message(client):
    """Actualiza el mensaje de estado en Telegram."""
    last_text = ""
    while True:
        try:
            if status_data["status_message"]:
                lines = ["**[ ESTADO DEL BOT ]**\n"]
                
                active_list = list(status_data["active"].values())
                
                if not active_list:
                    if status_data["total_in_queue"] > 0:
                        lines.append("-- Esperando para iniciar descargas --")
                    else:
                        lines.append("**Sin tareas activas.**")
                else:
                    for data in active_list:
                        speed = data.get("speed", 0)
                        speed_fmt = format_size(speed) + "/s"
                        downloaded_fmt = format_size(data.get("downloaded", 0))
                        total = data.get("total", 0)
                        total_fmt = format_size(total)
                        progress = data.get("progress", 0.0)
                        
                        filled = int(progress / 10)
                        bar = "[" + "=" * filled + "-" * (10 - filled) + "]"
                        
                        task_type = "BAJANDO" if data.get("type") == "download" else "SUBIENDO"
                        lines.append(f"**{task_type}: {data['filename']}**")
                        lines.append(f"{bar} {progress:.2f}%")
                        
                        eta_val = "..."
                        if speed > 0 and total > 0:
                            remaining = total - data.get("downloaded", 0)
                            eta_val = format_time(remaining / speed)
                        
                        lines.append(f"`{downloaded_fmt}` / `{total_fmt}` | `{speed_fmt}`")
                        lines.append(f"Queda: `{eta_val}`\n")
                
                lines.append(f"**Hechos:** {status_data['completed']}")
                lines.append(f"**Fallos:** {status_data['failed']}")
                lines.append(f"**En Cola:** {status_data['total_in_queue']}")
                
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

def download_file_worker(client, loop):
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
                    for chunk in response.iter_content(chunk_size=4096*1024):
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
                if retries < retry_max:
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

client_app = Client(
    "visuales_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TOKEN
)

@client_app.on_message(filters.command("main_menu"))
async def main_menu_handler(client, message):
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Comenzar", callback_data="start_bot")],
        [InlineKeyboardButton("Ajustes", callback_data="settings")]
    ])
    await message.reply("Elige una opción:", reply_markup=keyboard)

@client_app.on_message(filters.command("start"))
async def start_handler(client, message):
    print(f"[DEBUG] Comando /start recibido de {message.from_user.username if message.from_user else 'unknown'}")
    await message.reply("¡Hola! El bot está en línea.\n\n"
                        "Comandos disponibles:\n"
                        "/down <ruta> - Descarga desde Visuales UCLV\n"
                        "/yt <url> - Descarga desde YouTube\n"
                        "/status - Muestra el estado actual")

@client_app.on_message(filters.command("yt"))
async def yt_handler(client, message):
    print(f"[DEBUG] Comando /yt recibido: {message.text}")
    if len(message.command) < 2:
        await message.reply("Uso: /yt <url> [720, 1080, etc] [sub]")
        return
    
    url = message.command[1]
    quality = "best"
    include_subs = False
    
    if len(message.command) >= 3:
        for arg in message.command[2:]:
            if arg.isdigit():
                quality = f"bestvideo[height<={arg}]+bestaudio/best[height<={arg}]"
            elif arg.lower() in ["sub", "subs", "subtitulos"]:
                include_subs = True

    status_msg = await message.reply("Analizando video...")

    ydl_opts = {
        "format": quality,
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "writesubtitles": include_subs,
        "writeautomaticsub": include_subs,
        "subtitleslangs": ["es", "en"],
        "embedsubs": True,
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
                f"**INFO DEL VIDEO**\n"
                f"Titulo: `{title}`\n"
                f"Calidad: `{actual_res}`\n"
                f"Subs: `{'Si' if include_subs else 'No'}`\n"
                f"Canal: `{uploader}`\n"
                f"Duracion: `{duration}`\n"
                f"Vistas: `{views:,}`\n\n"
                f"Descargando..."
            )
            await status_msg.edit_text(metadata_text)
            
            task_key = f"dl_yt_{title[:20]}"
            
            last_edit_time = 0

            def progress_hook(d):
                nonlocal last_edit_time
                if d['status'] == 'downloading':
                    p_str = d.get('_percent_str', '0%').replace('%', '').strip()
                    try:
                        progress = float(p_str)
                    except:
                        progress = 0.0
                        
                    speed = d.get('speed', 0) or 0
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    
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
                        bar = "[" + "=" * filled + "-" * (10 - filled) + "]"
                        speed_fmt = format_size(speed) + "/s"
                        
                        msg_text = (
                            f"**DESCARGANDO YOUTUBE ({actual_res})**\n"
                            f"Archivo: `{title}`\n"
                            f"{bar} {progress:.2f}%\n"
                            f"`{format_size(downloaded)}` / `{format_size(total)}` | `{speed_fmt}`"
                        )
                        
                        asyncio.run_coroutine_threadsafe(
                            status_msg.edit_text(msg_text),
                            loop
                        )
                        last_edit_time = current_time

                elif d['status'] == 'finished':
                    if task_key in status_data["active"]:
                        del status_data["active"][task_key]

            ydl.add_progress_hook(progress_hook)
            
            await loop.run_in_executor(
                None,
                partial(ydl.download, [url])
            )
            
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            # Try to find it if extension changed
            base = filename.rsplit('.', 1)[0]
            found = False
            for ext in ['.mp4', '.webm', '.mkv']:
                if os.path.exists(base + ext):
                    filename = base + ext
                    found = True
                    break
            if not found:
                await status_msg.edit_text("Error: No se encontró el archivo descargado")
                return
        
        real_filename = os.path.basename(filename)
        await status_msg.edit_text(f"Encolando subida: {real_filename}")
        await upload_file(client, filename, real_filename)
        
    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)}")
        print(f"Error en yt: {e}")

@client_app.on_message(filters.command("status"))
async def status_handler(client, message):
    msg = await message.reply("Obteniendo estado...")
    status_data["status_message"] = msg

@client_app.on_message(filters.command("down"))
async def down_handler(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Uso: /down <Path>")
        return
    
    path_arg = message.text.split(None, 1)[1].strip('/')
    target_url = urljoin(BASE_URL, path_arg + "/")
    
    status_msg = await message.reply(f"Buscando archivos en: `{target_url}`")
    status_data["is_searching"] = True
    
    try:
        req = requests.get(target_url, timeout=120)
        req.raise_for_status()
        
        soup = BeautifulSoup(req.text, "html.parser")
        links = soup.find_all("a")
        
        found = 0
        skipped = 0
        
        processed = load_processed()
        
        folder_candidates = []
        for link in links:
            href = link.get("href")
            if not href or href.startswith("?") or "Parent Directory" in link.text:
                continue
            
            if href.endswith('/'):                
                folder_candidates.append(urljoin(target_url, href))
            elif href.lower().endswith(FORMATS):
                filename = unquote(href.split('/')[-1])
                if filename in processed:
                    skipped += 1
                    continue
                file_url = urljoin(target_url, href)
                download_queue.put((file_url, filename, 0))
                found += 1

        total_folders = len(folder_candidates)
        for i, sub_url in enumerate(folder_candidates, 1):
            try:
                if i % 3 == 0 or i == total_folders:
                    await status_msg.edit_text(f"Buscando archivos... ({i}/{total_folders} carpetas exploradas)\nEncontrados: `{found}`\nOmitidos: `{skipped}`")
                
                sub_req = requests.get(sub_url, timeout=120)
                sub_req.raise_for_status()
                sub_soup = BeautifulSoup(sub_req.text, "html.parser")
                
                for sub_link in sub_soup.find_all("a"):
                    sub_href = sub_link.get("href")
                    if not sub_href or sub_href.startswith("?") or "Parent Directory" in sub_link.text:
                        continue
                    
                    if sub_href.lower().endswith(FORMATS):
                        filename = unquote(sub_href.split('/')[-1])
                        if filename in processed:
                            skipped += 1
                            continue
                        file_url = urljoin(sub_url, sub_href)
                        download_queue.put((file_url, filename, 0))
                        found += 1
            except Exception as e:
                print(f"Error explorando carpetas (Read Timeout en {sub_url}): {e}")
        
        status_data["is_searching"] = False
        status_data["total_in_queue"] += found
        
        await status_msg.edit_text(f"Se han añadido {found} archivos a la cola.\nOmitidos por ya existir: {skipped}")
        
        if not status_data["status_message"]:
            status_data["status_message"] = await message.reply("Iniciando seguimiento de descargas...")
            
    except Exception as e:
        await status_msg.edit_text(f"Error: {e}")

def main():
    print("Iniciando bot...")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


    for _ in range(CANT_WORKER):
        threading.Thread(target=download_file_worker, args=(client_app, loop), daemon=True).start()

    asyncio.ensure_future(upload_worker(client_app), loop=loop)
    
    asyncio.ensure_future(update_status_message(client_app), loop=loop)
    
    print(f"Bot activo. Workers: Descarga={CANT_WORKER}, Subida={UPLOAD_WORKER}")
    
    
    for _ in range(UPLOAD_WORKER - 1):
        asyncio.ensure_future(upload_worker(client_app), loop=loop)
    

    client_app.run()

if __name__ == '__main__':
    main()
