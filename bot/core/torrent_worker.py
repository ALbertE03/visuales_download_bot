import libtorrent as lt
import time
import os
import asyncio
from bot.config import CONFIG
from bot.core.upload_worker import upload_file
from bot.constants import CONSTANTS

def download_torrent(client, loop, source):
    """
    Descarga un torrent desde un enlace magnet o una ruta a un archivo .torrent.
    :param source: Puede ser un enlace magnet o la ruta local a un archivo .torrent.
    """
    ses = lt.session({'listen_interfaces': CONSTANTS.LT_LISTEN_INTERFACES})
    
    params = {}
    if source.startswith("magnet:"):
        params = lt.parse_magnet_uri(source)
    else:
        # Es un archivo local .torrent
        info = lt.torrent_info(source)
        params = {
            'ti': info,
            'save_path': CONFIG.DOWNLOAD_DIR.value
        }

    if isinstance(params, dict):
        handle = ses.add_torrent(params)
    else:
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
        "type": CONSTANTS.TASK_TYPE_TORRENT
    }

    CONFIG.LOGGER.value.info(CONSTANTS.LOG_TORRENT_START.format(filename=filename))

    CONFIG.status_data.value["active"][task_key]["status"] = CONSTANTS.STATUS_METADATA

    while not handle.has_metadata():
        time.sleep(1)
        if task_key not in CONFIG.status_data.value["active"]:
            CONFIG.LOGGER.value.info(CONSTANTS.LOG_TORRENT_EXITING)
            ses.remove_torrent(handle)
            return
        CONFIG.LOGGER.value.info(CONSTANTS.LOG_TORRENT_METADATA_WAIT)
    
    CONFIG.LOGGER.value.info(CONSTANTS.LOG_TORRENT_METADATA_OK)
    torrent_info = handle.get_torrent_info()
    filename = torrent_info.name()
    CONFIG.status_data.value["active"][task_key]["filename"] = filename
    total_size = torrent_info.total_size()
    CONFIG.status_data.value["active"][task_key]["total"] = total_size
    CONFIG.status_data.value["active"][task_key]["status"] = CONSTANTS.MSG_DOWNLOADING

    while not handle.is_seed():
        s = handle.status()
        CONFIG.status_data.value["active"][task_key]["progress"] = s.progress * 100
        CONFIG.status_data.value["active"][task_key]["downloaded"] = s.total_done
        CONFIG.status_data.value["active"][task_key]["speed"] = s.download_rate
        CONFIG.status_data.value["active"][task_key]["seeds"] = s.num_seeds
        CONFIG.status_data.value["active"][task_key]["peers"] = s.num_peers
        CONFIG.status_data.value["active"][task_key]["list_seeds"] = s.list_seeds
        CONFIG.status_data.value["active"][task_key]["list_peers"] = s.list_peers
        
        if task_key not in CONFIG.status_data.value["active"]:
            ses.remove_torrent(handle)
            return
            
        time.sleep(1)

    CONFIG.LOGGER.value.info(CONSTANTS.LOG_TORRENT_FINISHED.format(filename=filename))
    
    file_path = os.path.join(CONFIG.DOWNLOAD_DIR.value, filename)
    
    video_extensions = CONFIG.FORMATS.value

    if os.path.isdir(file_path):
        CONFIG.LOGGER.value.info(CONSTANTS.LOG_TORRENT_FOLDER.format(filename=filename))
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.lower().endswith(video_extensions):
                    full_path = os.path.join(root, file)
                    asyncio.run_coroutine_threadsafe(
                        upload_file(client, full_path, file),
                        loop
                    )
                else:
                    CONFIG.LOGGER.value.info(CONSTANTS.LOG_SKIP_NON_VIDEO.format(file=file))
    else:
        if filename.lower().endswith(video_extensions):
            asyncio.run_coroutine_threadsafe(
                upload_file(client, file_path, filename),
                loop
            )
        else:
            CONFIG.LOGGER.value.info(CONSTANTS.LOG_SKIP_TORRENT_NON_VIDEO.format(filename=filename))

    
    if task_key in CONFIG.status_data.value["active"]:
        del CONFIG.status_data.value["active"][task_key]
    
    ses.remove_torrent(handle)
    
    if not source.startswith("magnet:") and os.path.exists(source):
        try:
            os.remove(source)
        except Exception:
            pass
