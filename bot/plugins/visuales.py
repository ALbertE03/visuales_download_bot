import requests
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from pyrogram import Client
from pyrogram.types import Message
from bot.config import BASE_URL, FORMATS, download_queue, status_data
from bot.utils import load_processed, load_explorer_cache, save_explorer_cache

async def down_handler(client: Client, message: Message) -> None:
    if len(message.command) < 2:
        await message.reply("Uso: /down <Path>")
        return
    
    path_arg = message.text.split(None, 1)[1].strip('/')
    target_url = urljoin(BASE_URL, path_arg + "/")
    
    status_msg = await message.reply(f"Buscando archivos en:\n{target_url}")
    status_data["is_searching"] = True
    
    persistent_cache = load_explorer_cache()
    cached_data = persistent_cache.get(target_url, [])

    already_scanned_urls = {item[0] for item in cached_data}
    

    processed = load_processed()
    found = 0
    skipped = 0
    
    current_cache = list(cached_data) 

    for file_url, filename in cached_data:
        if filename in processed:
            skipped += 1
            continue
        download_queue.put((file_url, filename, 0))
        found += 1
    
    if found > 0 or skipped > 0:
        await status_msg.edit_text(f"Cargados de cache: {found + skipped} archivos.\nContinuando exploración para detectar nuevos...")
 
    try:
        req = requests.get(target_url, timeout=120)
        req.raise_for_status()
        
        soup = BeautifulSoup(req.text, "html.parser")
        links = soup.find_all("a")
        
        folder_candidates = []
        for link in links:
            href = link.get("href")
            if not href or href.startswith("?") or "Parent Directory" in link.text:
                continue
            
            if href.endswith('/'):                
                folder_candidates.append(urljoin(target_url, href))
            elif href.lower().endswith(FORMATS):
                file_url = urljoin(target_url, href)
                
                
                if file_url in already_scanned_urls:
                    continue
                
                filename = unquote(href.split('/')[-1])
                current_cache.append((file_url, filename))
                already_scanned_urls.add(file_url) 
                
                if filename in processed:
                    skipped += 1
                    continue
                download_queue.put((file_url, filename, 0))
                found += 1

        total_folders = len(folder_candidates)
        for i, sub_url in enumerate(folder_candidates, 1):
            try:
                if i % 3 == 0 or i == total_folders:
                    await status_msg.edit_text(f"Buscando archivos...\n({i}/{total_folders} carpetas exploradas)\nEncontrados nuevos: {found}\nOmitidos/Cache: {skipped}")
                    save_explorer_cache(target_url, current_cache)
                
                sub_req = requests.get(sub_url, timeout=120)
                sub_req.raise_for_status()
                sub_soup = BeautifulSoup(sub_req.text, "html.parser")
                
                for sub_link in sub_soup.find_all("a"):
                    sub_href = sub_link.get("href")
                    if not sub_href or sub_href.startswith("?") or "Parent Directory" in sub_link.text:
                        continue
                    
                    if sub_href.lower().endswith(FORMATS):
                        file_url = urljoin(sub_url, sub_href)
                        
                        if file_url in already_scanned_urls:
                            continue
                            
                        filename = unquote(sub_href.split('/')[-1])
                        current_cache.append((file_url, filename))
                        already_scanned_urls.add(file_url)
                        
                        if filename in processed:
                            skipped += 1
                            continue
                        download_queue.put((file_url, filename, 0))
                        found += 1
            except requests.exceptions.RequestException as e:
                print(f"Error en carpeta {sub_url}: {e}")
        
       
        save_explorer_cache(target_url, current_cache)
        
        status_data["is_searching"] = False
        status_data["total_in_queue"] += found
        
        await status_msg.edit_text(f"Busqueda finalizada.\nAnadidos: {found}\nOmitidos por ya existir: {skipped}")
        
        if not status_data["status_message"]:
            status_data["status_message"] = await message.reply("Iniciando seguimiento de descargas...")
            
    except requests.exceptions.HTTPError as e:
        await status_msg.edit_text(f"Error de red: El servidor respondio con error {e.response.status_code}")
    except Exception as e:
        await status_msg.edit_text(f"Error inesperado: {str(e)}")
