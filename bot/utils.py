import math
import os
import json
from typing import Set, Dict, Any
from bot.config import CONFIG
import py7zr

def format_size(size_bytes: int) -> str:
    if size_bytes <= 0: return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def format_time(seconds: float) -> str:
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

def load_processed() -> Set[str]:
    if os.path.exists(CONFIG.PROCESSED_DB.value):
        try:
            with open(CONFIG.PROCESSED_DB.value, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def save_processed(filename: str) -> None:
    data = list(load_processed())
    if filename not in data:
        data.append(filename)
        with open(CONFIG.PROCESSED_DB.value, "w") as f: json.dump(data, f)

def load_explorer_cache() -> Dict[str, Any]:
    if os.path.exists(CONFIG.EXPLORER_CACHE_DB.value):
        try:
            with open(CONFIG.EXPLORER_CACHE_DB.value, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_explorer_cache(url: str, files: list) -> None:
    cache = load_explorer_cache()
    cache[url] = files
    with open(CONFIG.EXPLORER_CACHE_DB.value, "w") as f: json.dump(cache, f)


def split_file(file_path: str, chunk_size_mb: int = 1900) -> list[str]:
    """Divide un archivo en partes de un tamaÃ±o especÃ­fico usando py7zr."""
    chunk_size = chunk_size_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)
    
    if file_size <= chunk_size:
        return [file_path]
    
    output_parts = []
    base_name = file_path + ".7z"
    
    # py7zr supports multi-volume archives through setting volume_size
    with py7zr.SevenZipFile(base_name, 'w', volume_size=chunk_size) as archive:
        archive.write(file_path, arcname=os.path.basename(file_path))
    
    # py7zr generates files like filename.7z.001, filename.7z.002, etc.
    # We need to find all generated parts
    dir_path = os.path.dirname(file_path)
    base_filename = os.path.basename(base_name)
    
    for f in os.listdir(dir_path):
        if f.startswith(base_filename):
            output_parts.append(os.path.join(dir_path, f))
            
    output_parts.sort()
    
    return output_parts
