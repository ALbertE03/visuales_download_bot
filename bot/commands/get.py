import re
from pyrogram import Client
from pyrogram.types import Message
from bot.config import CONFIG
from bot.constants import CONSTANTS


async def get_handler(client: Client, message: Message) -> None:
    """Manejador para el comando /get [url]"""
    if len(message.command) < 2:
        await message.reply("Uso: `/get [url]`")
        return

    url = message.text.split(None, 1)[1].strip()

    filename = "downloaded_file"

    filename_match = re.search(r"filename=([^&]+)", url)
    if filename_match:
        filename = filename_match.group(1)
    else:
        url_path = url.split("?")[0]
        filename = url_path.split("/")[-1] or "downloaded_file"

    CONFIG.download_queue.value.put((url, filename, 0))
    CONFIG.status_data.value["total_in_queue"] += 1

    await message.reply(f"**Añadido a la cola:** `{filename}`")
