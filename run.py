import asyncio
from threading import Thread
from pyrogram import Client
from bot.config import API_ID, API_HASH, TOKEN, CANT_WORKER, UPLOAD_WORKER
from bot.core.download_worker import download_file_worker
from bot.core.upload_worker import upload_worker
from bot.core.update_status import update_status_message
from bot.plugins.general import start_handler, main_menu_handler, status_handler
from bot.plugins.youtube import yt_handler
from bot.plugins.visuales import down_handler
from pyrogram.handlers import MessageHandler
from pyrogram import filters


def main():
    print("Iniciando Bot...")

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Client("visuales_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN, sleep_threshold=60)

    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    app.add_handler(MessageHandler(main_menu_handler, filters.command("main_menu")))
    app.add_handler(MessageHandler(status_handler, filters.command("status")))
    app.add_handler(MessageHandler(yt_handler, filters.command("yt")))
    app.add_handler(MessageHandler(down_handler, filters.command("down")))

    for _ in range(CANT_WORKER):
        Thread(
            target=download_file_worker, args=(app, loop), daemon=True
        ).start()

    for _ in range(UPLOAD_WORKER):
        asyncio.ensure_future(upload_worker(app), loop=loop)

    asyncio.ensure_future(update_status_message(app), loop=loop)

    print(f"Bot activo. Workers: Descarga={CANT_WORKER}, Subida={UPLOAD_WORKER}")

    app.run()


if __name__ == "__main__":
    main()
