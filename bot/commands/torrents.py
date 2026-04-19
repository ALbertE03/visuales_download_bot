import asyncio
from pyrogram import Client
from pyrogram.types import  Message

async def torrent_handler(client: Client, message: Message) -> None:
    if len(message.command) < 2:
        await message.reply("Uso: /torrent <magnet_link>")
        return
    
    magnet_link = message.text.split(None, 1)[1].strip()
    if not magnet_link.startswith("magnet:?xt=urn:btih:"):
        await message.reply("Enlace magnet inválido.")
        return

    from bot.core.torrent_worker import download_torrent
    import threading
    
    await message.reply("Añadido a la cola de torrents.")
    
    loop = asyncio.get_event_loop()
    threading.Thread(target=download_torrent, args=(client, loop, magnet_link), daemon=True).start()
