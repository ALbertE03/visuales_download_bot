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


async def status_handler(client: Client, message: Message) -> None:
    msg = await message.reply(CONSTANTS.MSG_GETTING_STATUS)
    CONFIG.status_data.value["force_status_update"] = True
    CONFIG.status_data.value["status_message"] = msg
