from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot.config import CONFIG
import asyncio

async def main_menu_handler(client: Client, message: Message) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Comenzar", callback_data="start_bot")],
        [InlineKeyboardButton("Ajustes", callback_data="settings")]
    ])
    await message.reply("Elige una opcion:", reply_markup=keyboard)
    CONFIG.LOGGER.value.info(f"Bot start by {message.from_user.id}")

async def start_handler(client: Client, message: Message) -> None:
    await message.reply("Comandos disponibles:\n"
                        " - /down <ruta> - Descarga desde Visuales UCLV\n"
                        " - /yt <url> - Descarga desde YouTube\n"
                        " - /torrent <magnet_link> - Descarga un torrent (Magnet)\n"
                        " - /status - Panel de Control")

async def torrent_handler(client: Client, message: Message) -> None:
    if len(message.command) < 2:
        await message.reply("Uso: /torrent <magnet_link>")
        return
    
    magnet_link = message.text.split(None, 1)[1].strip()
    if not magnet_link.startswith("magnet:?xt=urn:btih:"):
        await message.reply("Enlace magnet invÃ¡lido.")
        return

    from bot.core.torrent_worker import download_torrent
    import threading
    
    await message.reply("AÃ±adido a la cola de torrents.")
    
    loop = asyncio.get_event_loop()
    threading.Thread(target=download_torrent, args=(client, loop, magnet_link), daemon=True).start()

async def status_handler(client: Client, message: Message) -> None:
    msg = await message.reply("Obteniendo estado...")
    CONFIG.status_data.value["status_message"] = msg
