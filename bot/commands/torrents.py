import asyncio
import os
import threading
from pyrogram import Client
from pyrogram.types import Message
from bot.constants import CONSTANTS
from bot.config import CONFIG

async def torrent_handler(client: Client, message: Message) -> None:
    magnet_link = None
    torrent_path = None
    
    # Si es un comando /torrent <magnet>
    if message.command and message.command[0] == "torrent":
        if len(message.command) < 2 and not message.document:
            await message.reply(CONSTANTS.MSG_CMD_TORRENT_USAGE)
            return
        if len(message.command) >= 2:
            text = message.text or message.caption
            magnet_link = text.split(None, 1)[1].strip()
            if not magnet_link.startswith("magnet:?xt=urn:btih:"):
                await message.reply(CONSTANTS.MSG_INVALID_MAGNET)
                return
    
    # Si es un archivo .torrent subido
    if message.document and message.document.file_name.endswith(".torrent"):
        status_msg = await message.reply(CONSTANTS.STATUS_DOWN_TORRENT)
        try:
            torrent_path = await message.download(file_name=os.path.join(CONSTANTS.DOWNLOAD_DIR, message.document.file_name))
            await status_msg.edit(CONSTANTS.MSG_GET_TORRENT_FILE_OK)
        except Exception as e:
            CONFIG.LOGGER.value.error(CONSTANTS.LOG_TORRENT_FILE_ERROR.format(error=str(e)))
            await status_msg.edit(CONSTANTS.MSG_INVALID_TORRENT_FILE)
            return
    

    from bot.core.torrent_worker import download_torrent
    
    await message.reply(CONSTANTS.MSG_ADDED_TORRENT_QUEUE)
    
    loop = asyncio.get_event_loop()
    threading.Thread(target=download_torrent, args=(client, loop, magnet_link or torrent_path, message.chat.id), daemon=True).start()
