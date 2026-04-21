import os
import streamlit as st
import queue
import asyncio
from typing import Dict, Any
from enum import Enum
from bot.log import logger
from bot.constants import CONSTANTS

class CONFIG(Enum):
    LOGGER = logger
    API_ID: int = int(st.secrets.get("API_ID", 0))
    API_HASH: str = st.secrets.get("API_HASH", "")
    TOKEN: str = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    _target_raw = st.secrets.get("TARGET_GROUP", "")
    try:
        TARGET_GROUP = int(_target_raw)
    except ValueError:
        TARGET_GROUP = _target_raw

    BASE_URL: str = st.secrets.get("BASE_URL", "https://visuales.uclv.cu/")
    DOWNLOAD_DIR: str = CONSTANTS.DOWNLOAD_DIR
    PROCESSED_DB: str = CONSTANTS.PROCESSED_DB
    EXPLORER_CACHE_DB: str = CONSTANTS.EXPLORER_CACHE_DB
    FORMATS: tuple = CONSTANTS.VIDEO_FORMATS

    CANT_WORKER: int = 2
    UPLOAD_WORKER: int = 2
    RETRY_MAX: int = 3

    status_data: Dict[str, Any] = {
        "active": {},  # {task_key: {filename, progress, speed, downloaded, total, type}}
        "completed": 0,
        "failed": 0,
        "total_in_queue": 0,
        "is_searching": False,
        "status_message": None,
    }

    download_queue: queue.Queue = queue.Queue()
    upload_queue: asyncio.Queue = asyncio.Queue()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
