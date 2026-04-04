
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

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_GROUP = os.getenv("TARGET_GROUP")
BASE_URL = os.getenv("BASE_URL", "https://visuales.uclv.cu/")
CANT_WORKER=3
DOWNLOAD_DIR = "downloads"
PROCESSED_DB = "processed.json"
FORMATS = ('.mp4', '.mkv', '.avi', '.mpg', '.dat', '.wmv', '.mov', '.mpg', '.mpeg')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)



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

async def upload_file(client, file_path, filename):
    """Sube archivos"""
   
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
            if elapsed > 0.1:
                status_data["active"][task_key]["speed"] = current / elapsed

        await client.send_document(
            chat_id=TARGET_GROUP,
            document=file_path,
            file_name=filename,
            caption=f"**{filename}**",
            progress=progress_callback
        )
        print(f"Finalizado: {filename} enviado.")
        
        save_processed(filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Archivo local eliminado: {filename}")
            
    except Exception as e:
        print(f"Error subiendo {filename}: {e}")
    finally:
        if task_key in status_data["active"]:
            del status_data["active"][task_key]

async def update_status_message(client):
    """Actualiza el mensaje de estado en Telegram."""
    last_text = ""
    while True:
        try:
            if status_data["status_message"]:
                lines = ["📊 **Estado de Descargas**\n"]
                
                active_list = list(status_data["active"].values())
                
                if not active_list:
                    if status_data["total_in_queue"] > 0:
                        lines.append("*Esperando para iniciar descargas...*")
                    else:
                        lines.append("*No hay descargas activas.*")
                else:
                    for data in active_list:
                        speed_fmt = format_size(data["speed"]) + "/s"
                        downloaded_fmt = format_size(data["downloaded"])
                        total_fmt = format_size(data["total"])
                        progress = data["progress"]
                        
                        filled = int(progress / 10)
                        bar = "■" * filled + "□" * (10 - filled)
                        
                        emoji = "📥" if data.get("type") == "download" else "📤"
                        lines.append(f"{emoji} **{data['filename']}**")
                        lines.append(f"{bar} {progress:.2f}%")
                        lines.append(f"`{downloaded_fmt}` / `{total_fmt}` | `{speed_fmt}`\n")
                
                lines.append(f"✅ **Completados:** {status_data['completed']}")
                lines.append(f"❌ **Fallidos:** {status_data['failed']}")
                lines.append(f"📋 **En cola restante:** {status_data['total_in_queue']}")
                
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
    """Procesador de la cola de descargas en un hilo separado."""
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
                    for chunk in response.iter_content(chunk_size=1024*1024):
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
                
                status_data["completed"] += 1
                
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

@client_app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply("Hola! Usa /down ruta para descargar o /status para ver el progreso.")

@client_app.on_message(filters.command("status"))
async def status_handler(client, message):
    msg = await message.reply("📊 Obteniendo estado...")
    status_data["status_message"] = msg

@client_app.on_message(filters.command("down"))
async def down_handler(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Uso: /down Peliculas/Cubanas")
        return
    
    path_arg = message.text.split(None, 1)[1].strip('/')
    target_url = urljoin(BASE_URL, path_arg + "/")
    
    status_msg = await message.reply(f"🔍 Buscando archivos en: `{target_url}`")
    status_data["is_searching"] = True
    
    try:
        req = requests.get(target_url, timeout=30)
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
                
                sub_req = requests.get(sub_url, timeout=50)
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
                print(f"Error explorando carpetas: {e}")
        
        status_data["is_searching"] = False
        status_data["total_in_queue"] += found
        
        await status_msg.edit_text(f"✅ Se han añadido {found} archivos a la cola.\nOmitidos por ya existir: {skipped}")
        
        if not status_data["status_message"]:
            status_data["status_message"] = await message.reply("📉 Iniciando seguimiento de descargas...")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")

def main():
    print("Iniciando bot...")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    for _ in range(CANT_WORKER):
        threading.Thread(target=download_file_worker, args=(client_app, loop), daemon=True).start()

    asyncio.run_coroutine_threadsafe(update_status_message(client_app), loop)
    
    print("Bot activo. Presiona Ctrl+C para salir.")
    client_app.run()

if __name__ == '__main__':
    main()
