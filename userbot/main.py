import streamlit as st
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

from userbot.commands.audio import totext_cmd, auto_transcribe_private
from userbot.commands.cine_filter import cine_filter_handler
from bot.commands.stream_cmd import stream_handler
from bot.log import logger

API_ID = st.secrets.get("API_ID")
API_HASH = st.secrets.get("API_HASH")
SESSION_STRING = st.secrets.get("SESSION_STRING", "")

if not API_ID or not API_HASH:
    print("Falta el API_ID o API_HASH en los secretos de Streamlit (secrets.toml)")
    exit(1)

if SESSION_STRING:
    userbot_app = Client(
        "my_userbot",
        session_string=SESSION_STRING,
        api_id=int(API_ID),
        api_hash=API_HASH,
        in_memory=True,
    )
else:
    userbot_app = Client(
        "my_userbot", api_id=int(API_ID), api_hash=API_HASH, workdir="userbot"
    )

async def userbot_stream_cmd(client: Client, message):
    logger.info(f"Comando /stream activado por userbot en el chat {message.chat.id}")
    await stream_handler(client, message)

userbot_app.add_handler(
    MessageHandler(totext_cmd, filters.command("totext", prefixes="/") & filters.me)
)

userbot_app.add_handler(
    MessageHandler(userbot_stream_cmd, filters.command("stream", prefixes="/") & filters.me)
)

userbot_app.add_handler(
    MessageHandler(
        auto_transcribe_private,
        filters.private
        & ~filters.me
        & ~filters.chat("MusicsHuntersbot")
        & (
            filters.voice
            | filters.video_note
            | filters.audio
            | (filters.document & filters.regex(r"audio/.*"))
        )
    )
)

userbot_app.add_handler(
    MessageHandler(
        cine_filter_handler,
        filters.chat("chat1080p") & filters.regex(r"(?i)^#cine") & ~filters.me
    )
)
