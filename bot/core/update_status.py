import asyncio
from bot.config import CONFIG 
from bot.utils import format_size, format_time
from pyrogram import Client

async def update_status_message(client: Client) -> None:
    """Actualiza el mensaje de estado en Telegram."""
    last_text = ""
    while True:
        try:
            if CONFIG.status_data.value["status_message"]:
                lines = ["[ PANEL DE CONTROL ]\n"]
                active_list = list(CONFIG.status_data.value["active"].values())
                
                if not active_list:
                    if CONFIG.status_data.value["total_in_queue"] > 0:
                        lines.append("Esperando para iniciar tareas...")
                    else:
                        lines.append("Sin tareas activas en este momento.")
                else:
                    for data in active_list:
                        speed = data.get("speed", 0)
                        speed_fmt = format_size(speed) + "/s"
                        downloaded_fmt = format_size(data.get("downloaded", 0))
                        total = data.get("total", 0)
                        total_fmt = format_size(total)
                        progress = data.get("progress", 0.0)
                        
                        filled = int(progress / 10)
                        bar = "▰" * filled + "▱" * (10 - filled)
                        
                        task_type = "DESCARGANDO" if data.get("type") == "download" else "SUBIENDO"
                        lines.append(f"== {task_type} ==")
                        lines.append(f"Archivo: {data['filename']}")
                        lines.append(f"[{bar}] {progress:.1f}%")
                        
                        eta_val = "calculando..."
                        if speed > 0 and total > 0:
                            remaining = total - data.get("downloaded", 0)
                            eta_val = format_time(remaining / speed)
                        
                        lines.append(f"{downloaded_fmt} de {total_fmt}")
                        lines.append(f"Velocidad: {speed_fmt}")
                        lines.append(f"Restante: {eta_val}\n")
                
                lines.append("-" * 15)
                lines.append(f"Completados: {CONFIG.status_data.value['completed']}")
                lines.append(f"Fallidos: {CONFIG.status_data.value['failed']}")
                lines.append(f"En Cola: {CONFIG.status_data.value['total_in_queue']}")
                
                txt = "\n".join(lines)
                
                if txt != last_text:
                    try:
                        await CONFIG.status_data.value["status_message"].edit_text(txt)
                        last_text = txt
                    except Exception as e:
                        if "MESSAGE_ID_INVALID" in str(e) or "MESSAGE_NOT_MODIFIED" not in str(e):
                            pass
            
            await asyncio.sleep(4)
        except Exception as e:
            CONFIG.LOGGER.value.error(f"Error en bucle de status: {e}")
            await asyncio.sleep(5)
