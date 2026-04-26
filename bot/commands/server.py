import sys
import time
import platform
import psutil
import pyrogram
from pyrogram import Client
from pyrogram.types import Message
from bot.utils import format_size, format_time


async def server_status(client: Client, message: Message):
    uptime = format_time(time.time() - psutil.boot_time())
    cpu_usage = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count()

    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    sms = "<b>[ ESTADO DEL SERVIDOR ]</b>\n"
    sms += "<blockquote>"
    sms += f"<b>SO:</b> <code>{platform.system()} {platform.release()}</code>\n"
    sms += f"<b>Arq:</b> <code>{platform.machine()}</code>\n"
    sms += f"<b>Uptime:</b> <code>{uptime}</code>"
    sms += "</blockquote>\n\n"

    sms += "<b>⎯⎯ RENDIMIENTO ⎯⎯</b>\n"
    sms += "<blockquote>"
    sms += f"<b>CPU ({cpu_count} núcleos):</b> <code>{cpu_usage}%</code>\n"
    sms += f"<b>RAM:</b> <code>{format_size(ram.used)} / {format_size(ram.total)} ({ram.percent}%)</code>\n"
    sms += f"<b>Disponible:</b> <code>{format_size(ram.available)}</code>"
    sms += "</blockquote>\n\n"

    sms += "<b>⎯⎯ ALMACENAMIENTO ⎯⎯</b>\n"
    sms += "<blockquote>"
    sms += f"<b>Disco (/):</b> <code>{format_size(disk.used)} / {format_size(disk.total)} ({disk.percent}%)</code>\n"
    sms += f"<b>Libre:</b> <code>{format_size(disk.free)}</code>"
    sms += "</blockquote>\n\n"

    sms += "<b>⎯⎯ RED ⎯⎯</b>\n"
    sms += "<blockquote>"
    sms += f"<b>Subido:</b> <code>{format_size(net.bytes_sent)}</code>\n"
    sms += f"<b>Descargado:</b> <code>{format_size(net.bytes_recv)}</code>"
    sms += "</blockquote>\n\n"

    await message.reply(sms)
