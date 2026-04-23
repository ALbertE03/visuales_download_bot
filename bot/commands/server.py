
from pyrogram import Client, Message
import psutil

async def server_status(client: Client, message: Message):
    sms ='Estado del Servidor:\n\n'
    disk_usage = psutil.disk_usage('/')
    sms += f"Espacio total: {disk_usage.total / (1024**3):.2f} GB\n"
    sms += f"Espacio usado: {disk_usage.used / (1024**3):.2f} GB\n"
    sms += f"Espacio libre: {disk_usage.free / (1024**3):.2f} GB\n"
    sms += f"Porcentaje usado: {disk_usage.percent}%\n\n"

    ram = psutil.virtual_memory()
    sms += f"RAM libre: {ram.available / (1024**3):.2f} GB\n"

    await message.reply(sms)