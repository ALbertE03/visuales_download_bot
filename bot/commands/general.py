from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot.config import CONFIG
from bot.constants import CONSTANTS


async def main_menu_handler(client: Client, message: Message) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONSTANTS.MSG_START_BUTTON, callback_data="start_bot")],
        [InlineKeyboardButton(CONSTANTS.MSG_SETTINGS_BUTTON, callback_data="settings")]
    ])
    await message.reply(CONSTANTS.MSG_CHOOSE_OPTION, reply_markup=keyboard)
    CONFIG.LOGGER.value.info(f"Bot iniciado por {message.from_user.id}")

async def start_handler(client: Client, message: Message) -> None:
    await message.reply(CONSTANTS.MSG_HELP)

async def cancel_handler(client: Client, message: Message) -> None:
    active_tasks = list(CONFIG.status_data.value["active"].items())
    if not active_tasks:
        await message.reply("No hay tareas activas para cancelar.")
        return

    buttons = []
    for task_key, data in active_tasks:
        name = data.get("filename", task_key)[:30]
        buttons.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"cancel_{task_key}")])
    
    buttons.append([InlineKeyboardButton("🛑 Cancelar TODAS", callback_data="cancel_all")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("Selecciona la tarea a cancelar:", reply_markup=reply_markup)

async def cancel_callback_handler(client: Client, callback_query) -> None:
    data = callback_query.data
    if data == "cancel_all":
        # Limpiar colas de descargas y subidas
        while not CONFIG.download_queue.value.empty():
            try:
                CONFIG.download_queue.value.get_nowait()
                CONFIG.download_queue.value.task_done()
            except Exception:
                pass
        
        while not CONFIG.upload_queue.value.empty():
            try:
                CONFIG.upload_queue.value.get_nowait()
                CONFIG.upload_queue.value.task_done()
            except Exception:
                pass
        
        # Eliminar las activas (esto lanzará CancelledError / ValueError)
        CONFIG.status_data.value["active"].clear()
        CONFIG.status_data.value["total_in_queue"] = 0
        
        await callback_query.message.edit_text("✅ Todas las tareas y la cola han sido canceladas.")
        CONFIG.LOGGER.value.info("El usuario canceló todas las tareas.")
        
    elif data.startswith("cancel_"):
        task_key = data.replace("cancel_", "")
        if task_key in CONFIG.status_data.value["active"]:
            name = CONFIG.status_data.value["active"][task_key].get("filename", task_key)
            del CONFIG.status_data.value["active"][task_key]
            await callback_query.answer(f"Cancelando: {name}", show_alert=True)
            await callback_query.message.delete()
            CONFIG.LOGGER.value.info(f"El usuario canceló la tarea: {task_key}")
        else:
            await callback_query.answer("La tarea ya no existe o terminó.", show_alert=True)

async def status_handler(client: Client, message: Message) -> None:
    msg = await message.reply(CONSTANTS.MSG_GETTING_STATUS)
    CONFIG.status_data.value["force_status_update"] = True
    CONFIG.status_data.value["status_message"] = msg
