import re
from pyrogram import Client
from pyrogram.types import Message

processed_cine_msgs = set()

async def cine_filter_handler(client: Client, message: Message):

    if message.id in processed_cine_msgs:
        return
    processed_cine_msgs.add(message.id)

    if len(processed_cine_msgs) > 500:
        processed_cine_msgs.clear()

    if not message.text and not message.caption:
        return

    if not message.photo and not message.document:
        await message.reply_text("es con una foto")
        return
    