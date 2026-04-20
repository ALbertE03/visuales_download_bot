import asyncio
from bot.config import CONFIG 
from bot.utils import format_size, format_time
from bot.constants import CONSTANTS
from pyrogram import Client

async def update_status_message(client: Client) -> None:
    """Actualiza el mensaje de estado en Telegram."""
    last_text = ""
    while True:
        try:
            if CONFIG.status_data.value["status_message"]:
                lines = [CONSTANTS.PANEL_HEADER]
                active_list = list(CONFIG.status_data.value["active"].values())
                
                if not active_list:
                    if CONFIG.status_data.value["total_in_queue"] > 0:
                        lines.append(CONSTANTS.STATUS_WAITING)
                    else:
                        lines.append(CONSTANTS.STATUS_NO_TASKS)
                else:
                    for data in active_list:
                        speed = data.get("speed", 0)
                        speed_fmt = format_size(speed) + "/s"
                        downloaded_fmt = format_size(data.get("downloaded", 0))
                        total = data.get("total", 0)
                        total_fmt = format_size(total)
                        progress = data.get("progress", 0.0)
                        status_info = data.get("status", "")
                        
                        filled = int(progress / 10)
                        bar = "▰" * filled + "▱" * (10 - filled)
                        
                        task_type_map = {
                            "download": CONSTANTS.TYPE_DOWNLOAD,
                            "upload": CONSTANTS.TYPE_UPLOAD,
                            "torrent": CONSTANTS.TYPE_TORRENT,
                        }
                        task_type = task_type_map.get(data.get("type"), CONSTANTS.TYPE_GENERIC)
                        
                        lines.append(CONSTANTS.PANEL_TASK_HEADER.format(task_type=task_type))
                        lines.append(CONSTANTS.PANEL_FILENAME.format(filename=data['filename']))
                        if status_info:
                            lines.append(CONSTANTS.PANEL_STATUS.format(status=status_info))
                        lines.append(CONSTANTS.PANEL_PROGRESS_BAR.format(bar=bar, progress=progress))
                        
                        eta_val = CONSTANTS.STATUS_CALCULATING
                        if speed > 0 and total > 0:
                            remaining = total - data.get("downloaded", 0)
                            eta_val = format_time(remaining / speed)
                        
                        lines.append(CONSTANTS.PANEL_UP_TO_DATE.format(downloaded=downloaded_fmt, total=total_fmt))
                        lines.append(CONSTANTS.PANEL_SPEED.format(speed=speed_fmt))
                        lines.append(CONSTANTS.PANEL_ETA.format(eta=eta_val))
                
                lines.append(CONSTANTS.PANEL_DIVIDER)
                lines.append(CONSTANTS.PANEL_COMPLETED.format(completed=CONFIG.status_data.value['completed']))
                lines.append(CONSTANTS.PANEL_FAILED.format(failed=CONFIG.status_data.value['failed']))
                lines.append(CONSTANTS.PANEL_QUEUE.format(queue=CONFIG.status_data.value['total_in_queue']))
                
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
            CONFIG.LOGGER.value.error(CONSTANTS.LOG_STATUS_LOOP_ERROR.format(error=e))
            await asyncio.sleep(5)
