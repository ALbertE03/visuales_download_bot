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
    provider = manager.get_provider(url)
    
    if not provider:
        await message.reply(CONSTANTS.MSG_NO_PROVIDER)
        return
    
    filename = url.split('/')[-1] or "file"
    
    CONFIG.download_queue.value.put((url, filename, 0))
    await message.reply(CONSTANTS.MSG_ADDED_QUEUE.format(filename=filename))

async def get_handler(client: Client, message: Message) -> None:
    if len(message.command) < 2:
        await message.reply(CONSTANTS.MSG_CMD_GET_USAGE)
        return
    
    url = message.text.split(None, 1)[1].strip()
    
    # Extraer nombre del archivo de la URL
    filename = url.split('/')[-1] or "direct_file"
    if '?' in filename:
        filename = filename.split('?')[0]
        
    CONFIG.download_queue.value.put((url, filename, 0))
    await message.reply(CONSTANTS.MSG_ADDED_QUEUE.format(filename=filename))
