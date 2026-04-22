import asyncio
import time
from bot.config import CONFIG
from bot.utils import format_size, format_time
from bot.constants import CONSTANTS
from pyrogram import Client
import streamlit as st

START_TIME = time.time()


async def update_status_message(client: Client) -> None:
    """Actualiza el mensaje de estado en Telegram."""
    last_text = ""
    last_message_id = None

    while True:
        try:
            current_status_msg = CONFIG.status_data.value.get("status_message")
            if current_status_msg:
                lines = [CONSTANTS.PANEL_HEADER]
                active_list = list(CONFIG.status_data.value["active"].values())
                queue_count = CONFIG.status_data.value["total_in_queue"]

                lines.append(
                    CONSTANTS.PANEL_ACTIVE_TASKS_HEADER.format(
                        active_count=len(active_list)
                    )
                )

                if not active_list:
                    if queue_count > 0:
                        lines.append(CONSTANTS.STATUS_WAITING)
                    else:
                        lines.append(CONSTANTS.PANEL_NO_TASKS)
                else:
                    for data in active_list:
                        speed = data.get("speed", 0)
                        speed_fmt = format_size(speed) + "/s"
                        downloaded_fmt = format_size(data.get("downloaded", 0))
                        total = data.get("total", 0)
                        total_fmt = format_size(total)
                        progress = data.get("progress", 0.0)
                        status_info = data.get("status", "")

                        filled = int(progress / 6.25)
                        bar = "█" * filled + "▒" * (16 - filled)

                        task_type_map = {
                            "download": CONSTANTS.TYPE_DOWNLOAD,
                            "upload": CONSTANTS.TYPE_UPLOAD,
                            "torrent": CONSTANTS.TYPE_TORRENT,
                            "split": "COMPRESIÓN ZIP",
                        }
                        task_type = task_type_map.get(
                            data.get("type", ""),
                            data.get("type", CONSTANTS.TYPE_GENERIC),
                        )

                        eta_val = "--"
                        if speed > 0 and total > 0:
                            remaining = max(0, total - data.get("downloaded", 0))
                            eta_val = format_time(remaining / speed)
                        elif total == 0:
                            eta_val = "Calculando..."

                        task_str = CONSTANTS.PANEL_TASK_ITEM.format(
                            task_type=task_type,
                            filename=data["filename"],
                            bar=bar,
                            progress=progress,
                            downloaded=downloaded_fmt,
                            total=total_fmt,
                            speed=speed_fmt,
                            eta=eta_val,
                        )

                        if data.get("type") == "torrent" and "seeds" in data:
                            seeds = data["seeds"]
                            peers = data["peers"]
                            list_seeds = data.get("list_seeds", 0)
                            list_peers = data.get("list_peers", 0)
                            tor_info = f"\n<b>Pares:</b> <code>{peers} ({list_peers})</code> | <b>Semillas:</b> <code>{seeds} ({list_seeds})</code>"
                            task_str = task_str.replace(
                                "</blockquote>", f"{tor_info}</blockquote>"
                            )

                        if status_info:
                            task_str = task_str.replace(
                                "</blockquote>",
                                f"\n<b>Extra:</b> <code>{status_info}</code></blockquote>",
                            )

                        lines.append(task_str)

                uptime_str = format_time(time.time() - START_TIME)
                completed = CONFIG.status_data.value["completed"]
                failed = CONFIG.status_data.value["failed"]

                if current_status_msg.chat.id == st.secrets.get("ADMIN_ID", 0):
                    lines.append(CONSTANTS.PANEL_GLOBAL_HEADER)
                    lines.append(
                        CONSTANTS.PANEL_GLOBAL_STATS.format(
                            uptime=uptime_str,
                            completed=completed,
                            failed=failed,
                            queue=queue_count,
                        )
                    )

                txt = "\n".join(lines)

                force_update = CONFIG.status_data.value.pop(
                    "force_status_update", False
                )

                if (
                    txt != last_text
                    or current_status_msg.id != last_message_id
                    or force_update
                ):
                    try:
                        await current_status_msg.edit_text(txt)
                        last_text = txt
                        last_message_id = current_status_msg.id
                    except Exception as e:
                        if "MESSAGE_ID_INVALID" in str(
                            e
                        ) or "MESSAGE_NOT_MODIFIED" not in str(e):
                            pass

            await asyncio.sleep(4)
        except Exception as e:
            CONFIG.LOGGER.value.error(CONSTANTS.LOG_STATUS_LOOP_ERROR.format(error=e))
            await asyncio.sleep(5)
