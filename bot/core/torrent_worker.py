import libtorrent as lt
import time
import os
import asyncio
from bot.config import CONFIG
from bot.core.upload_worker import upload_file

def download_torrent(client, loop, magnet_link):
    """Descarga un torrent desde un enlace magnet."""
    ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
    
    params = lt.parse_magnet_uri(magnet_link)
    params.save_path = CONFIG.DOWNLOAD_DIR.value
    handle = ses.add_torrent(params)
    
    filename = handle.status().name or "torrent_download"
    task_key = f"dl_{filename}"
    
    CONFIG.status_data.value["active"][task_key] = {
        "filename": filename,
        "progress": 0.0,
        "speed": 0.0,
        "downloaded": 0,
        "total": 0,
        "type": "torrent"
    }

    CONFIG.LOGGER.value.info(f"Iniciando descarga de torrent: {filename}")

    CONFIG.status_data.value["active"][task_key]["status"] = "Recopilando información (Metadata)..."

    while not handle.has_metadata():
        time.sleep(1)
        if task_key not in CONFIG.status_data.value["active"]:
            CONFIG.LOGGER.value.info("saliendo...")
            ses.remove_torrent(handle)
            return
        CONFIG.LOGGER.value.info("esperado metadata")
    
    CONFIG.LOGGER.value.info("Metadata obtenida")
    torrent_info = handle.get_torrent_info()
    filename = torrent_info.name()
    CONFIG.status_data.value["active"][task_key]["filename"] = filename
    total_size = torrent_info.total_size()
    CONFIG.status_data.value["active"][task_key]["total"] = total_size
    CONFIG.status_data.value["active"][task_key]["status"] = "Descargando..."

    while not handle.is_seed():
        s = handle.status()
        CONFIG.status_data.value["active"][task_key]["progress"] = s.progress * 100
        CONFIG.status_data.value["active"][task_key]["downloaded"] = s.total_done
        CONFIG.status_data.value["active"][task_key]["speed"] = s.download_rate
        
        if task_key not in CONFIG.status_data.value["active"]:
            ses.remove_torrent(handle)
            return
            
        time.sleep(1)

    CONFIG.LOGGER.value.info(f"Torrent {filename} descargado completamente.")
    
    file_path = os.path.join(CONFIG.DOWNLOAD_DIR.value, filename)
    
    video_extensions = CONFIG.FORMATS.value

    if os.path.isdir(file_path):
        CONFIG.LOGGER.value.info(f"Torrent {filename} es una carpeta, filtrando videos para subir...")
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.lower().endswith(video_extensions):
                    full_path = os.path.join(root, file)
                    asyncio.run_coroutine_threadsafe(
                        upload_file(client, full_path, file),
                        loop
                    )
                else:
                    CONFIG.LOGGER.value.info(f"Omitiendo archivo no vÃ­deo: {file}")
    else:
        if filename.lower().endswith(video_extensions):
            asyncio.run_coroutine_threadsafe(
                upload_file(client, file_path, filename),
                loop
            )
        else:
            CONFIG.LOGGER.value.info(f"Archivo torrent omitido por no ser video: {filename}")
    
    if task_key in CONFIG.status_data.value["active"]:
        del CONFIG.status_data.value["active"][task_key]
    
    ses.remove_torrent(handle)
