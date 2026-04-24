import re
from urllib.parse import unquote
from pyrogram import Client
from pyrogram.types import Message
from bot.manager import manager
from bot.config import CONFIG
from bot.constants import CONSTANTS


async def download_handler(client: Client, message: Message) -> None:
    if len(message.command) < 2:
        await message.reply(CONSTANTS.MSG_CMD_DOWNLOAD_USAGE)
        return

    url = message.text.split(None, 1)[1].strip()

    filename = "downloaded_file"
    filename_match = re.search(r"filename=([^&]+)", url)
    if filename_match:
        filename = unquote(filename_match.group(1))
    else:
        url_path = url.split("?")[0]
        filename = unquote(url_path.split("/")[-1]) or "downloaded_file"

    CONFIG.download_queue.value.put((url, filename, 0))
    CONFIG.status_data.value["total_in_queue"] += 1

    await message.reply(CONSTANTS.MSG_ADDED_QUEUE.format(filename=filename))
