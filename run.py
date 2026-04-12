import asyncio
from threading import Thread
from pyrogram import Client
from bot.config import CONFIG
from bot.core.download_worker import download_file_worker
from bot.core.upload_worker import upload_worker
from bot.core.update_status import update_status_message
from bot.commands.general import start_handler, main_menu_handler, status_handler
from bot.commands.youtube import yt_handler
from bot.commands.visuales import down_handler
from pyrogram.handlers import MessageHandler
from pyrogram import filters


def main():
    CONFIG.LOGGER.value.info("Iniciando Bot...")

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Client("visuales_bot", api_id=CONFIG.API_ID.value, api_hash=CONFIG.API_HASH.value, bot_token=CONFIG.TOKEN.value, sleep_threshold=120, max_concurrent_transmissions=2)

    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    app.add_handler(MessageHandler(main_menu_handler, filters.command("main_menu")))
    app.add_handler(MessageHandler(status_handler, filters.command("status")))
    app.add_handler(MessageHandler(yt_handler, filters.command("yt")))
    app.add_handler(MessageHandler(down_handler, filters.command("down")))

    for _ in range(CONFIG.CANT_WORKER.value):
        Thread(
            target=download_file_worker, args=(app, loop), daemon=True
        ).start()

    for _ in range(CONFIG.UPLOAD_WORKER.value):
        asyncio.ensure_future(upload_worker(app), loop=loop)

    asyncio.ensure_future(update_status_message(app), loop=loop)

    CONFIG.LOGGER.value.info(f"Bot activo. Workers: Descarga={CONFIG.CANT_WORKER.value}, Subida={CONFIG.UPLOAD_WORKER.value}")

    app.run()


if __name__ == "__main__":
    main()
