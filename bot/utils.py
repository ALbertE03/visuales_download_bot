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
        os.makedirs(os.path.dirname(CONFIG.PROCESSED_DB.value), exist_ok=True)
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
    os.makedirs(os.path.dirname(CONFIG.EXPLORER_CACHE_DB.value), exist_ok=True)
    with open(CONFIG.EXPLORER_CACHE_DB.value, "w") as f: json.dump(cache, f)


import subprocess

def split_file(file_path: str, chunk_size_mb: int = 1900) -> list[str]:
    """Divide un archivo en partes generando zip multivolumen para WinRAR usando comandos del sistema."""
    chunk_size = chunk_size_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)
    if file_size <= chunk_size:
        return [file_path]
    
    dir_path = os.path.dirname(file_path)
    zip_name = file_path + ".zip"
    
    try:
        # -s: chunk size, -0: cero compresión, -j: no guardar ruta completa
        cmd = ["zip", "-s", f"{chunk_size_mb}m", "-0", "-j", zip_name, file_path]
        subprocess.run(cmd, check=True)
    except Exception as e:
        CONFIG.LOGGER.value.error(f"Error comprimiendo en zip: {e}")
        return [file_path]
        
    output_parts = []
    base_zip_name = os.path.basename(zip_name)
    prefix = base_zip_name[:-4]
    
    for f in os.listdir(dir_path):
        if f.startswith(prefix) and (f.endswith(".zip") or ".z" in f):
            output_parts.append(os.path.join(dir_path, f))
            
    output_parts.sort()
    return output_parts
