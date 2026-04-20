import os
from dotenv import load_dotenv
import queue
import asyncio
from typing import Dict, Any
from enum import Enum
from bot.log import logger
from bot.constants import CONSTANTS


load_dotenv()

class CONFIG(Enum):
    LOGGER = logger
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TARGET_GROUP: str = os.getenv("TARGET_GROUP", "")


    BASE_URL: str = os.getenv("BASE_URL", "https://visuales.uclv.cu/")
    DOWNLOAD_DIR: str = CONSTANTS.DOWNLOAD_DIR
    PROCESSED_DB: str = CONSTANTS.PROCESSED_DB
    EXPLORER_CACHE_DB: str = CONSTANTS.EXPLORER_CACHE_DB
    FORMATS: tuple = CONSTANTS.VIDEO_FORMATS

    CANT_WORKER: int = 2
    UPLOAD_WORKER: int = 2
    RETRY_MAX: int = 3


    status_data: Dict[str, Any] = {
        "active": {}, # {task_key: {filename, progress, speed, downloaded, total, type}}
        "completed": 0,
        "failed": 0,
        "total_in_queue": 0,
        "is_searching": False,  
        "status_message": None
    }

    download_queue: queue.Queue = queue.Queue()
    upload_queue: asyncio.Queue = asyncio.Queue()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
