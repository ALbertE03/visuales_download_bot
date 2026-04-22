import asyncio
from threading import Thread
from pyrogram import Client
from bot.config import CONFIG
from bot.core.download_worker import download_file_worker
from bot.core.upload_worker import upload_worker
from bot.core.update_status import update_status_message
from bot.commands.general import start_handler, main_menu_handler, status_handler
from bot.commands.github import (
    ghuser_handler,
    ghrepo_handler,
    ghsearch_handler,
    ghcreate_handler
)
from bot.commands.torrents import torrent_handler
from bot.commands.visuales import down_handler
from bot.commands.download import download_handler
from bot.commands.collection import add_handler, end_handler, collection_monitor_handler
from pyrogram.handlers import MessageHandler
from pyrogram import filters
from userbot.main import userbot_app

def setup_bots():
    CONFIG.LOGGER.value.info("Configurando Bots...")

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = Client(
        "visuales_bot",
        api_id=CONFIG.API_ID.value,
        api_hash=CONFIG.API_HASH.value,
        bot_token=CONFIG.TOKEN.value,
        sleep_threshold=120,
        max_concurrent_transmissions=2,
    )

    app.add_handler(MessageHandler(start_handler, filters.command("start")))
    app.add_handler(MessageHandler(main_menu_handler, filters.command("main_menu")))
    app.add_handler(MessageHandler(status_handler, filters.command("status")))
    app.add_handler(MessageHandler(ghuser_handler, filters.command("ghuser")))
    app.add_handler(MessageHandler(ghrepo_handler, filters.command("ghrepo")))
    app.add_handler(MessageHandler(ghsearch_handler, filters.command("ghsearch")))
    app.add_handler(MessageHandler(ghcreate_handler, filters.command("ghcreate")))
    app.add_handler(
        MessageHandler(
            download_handler, filters.command("dl")
        )
    )
    app.add_handler(MessageHandler(down_handler, filters.command("down")))
    app.add_handler(
        MessageHandler(
            torrent_handler,
            filters.command("torrent")
            | (filters.document & filters.regex(r".*\.torrent$")),
        )
    )
    app.add_handler(MessageHandler(add_handler, filters.command("add")))
    app.add_handler(MessageHandler(end_handler, filters.command("end")))
    app.add_handler(MessageHandler(collection_monitor_handler, ~filters.command(["add", "end", "start", "main_menu", "status", "dl", "down", "torrent"])), group=1)

    for _ in range(CONFIG.CANT_WORKER.value):
        Thread(target=download_file_worker, args=(app, loop), daemon=True).start()

    for _ in range(CONFIG.UPLOAD_WORKER.value):
        asyncio.ensure_future(upload_worker(app), loop=loop)

    asyncio.ensure_future(update_status_message(app), loop=loop)

    CONFIG.LOGGER.value.info(
        f"Bot y Userbot activos. Workers: Descarga={CONFIG.CANT_WORKER.value}, Subida={CONFIG.UPLOAD_WORKER.value}"
    )

    def run_loop():
        asyncio.set_event_loop(loop)
        
        background_tasks = set()
        original_create_task = asyncio.create_task
        original_loop_create_task = loop.create_task
        
        def create_task_patch(coro, *args, **kwargs):
            task = original_create_task(coro, *args, **kwargs)
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
            return task
            
        def loop_create_task_patch(coro, *args, **kwargs):
            task = original_loop_create_task(coro, *args, **kwargs)
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
            return task
            
        asyncio.create_task = create_task_patch
        loop.create_task = loop_create_task_patch
        
        async def start_clients():
            await app.start()
            await userbot_app.start()
            
        loop.run_until_complete(start_clients())
        loop.run_forever()

    Thread(target=run_loop, daemon=True).start()
    
    return app, userbot_app

