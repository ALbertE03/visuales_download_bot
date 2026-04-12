from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot.config import CONFIG

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
                        " - /status - Panel de Control")

async def status_handler(client: Client, message: Message) -> None:
    msg = await message.reply("Obteniendo estado...")
    CONFIG.status_data.value["status_message"] = msg
