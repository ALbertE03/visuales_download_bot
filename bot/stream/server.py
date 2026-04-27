import time
import logging
import mimetypes
from collections import defaultdict

from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine

from bot.stream import StartTime, __version__
from bot.stream.config import StreamConfig
from bot.stream.file_properties import pack_file, get_short_hash
from bot.stream.streamer import PyrogramStreamer

logger = logging.getLogger("visuales_bot")

routes = web.RouteTableDef()

_streamer: PyrogramStreamer = None
_ongoing_requests: dict[str, int] = defaultdict(lambda: 0)


def init_streamer(client):
    """Inicializa el streamer con el cliente de Pyrogram."""
    global _streamer
    _streamer = PyrogramStreamer(client)


def _get_requester_ip(request: web.Request) -> str:
    try:
        return request.headers["X-Forwarded-For"].split(", ")[0]
    except KeyError:
        peername = request.transport.get_extra_info("peername")
        if peername is not None:
            return peername[0]
        return "unknown"


def _allow_request(ip: str) -> bool:
    return _ongoing_requests[ip] < StreamConfig.REQUEST_LIMIT


def _get_readable_time(seconds: float) -> str:
    count = 0
    readable_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", " días"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        readable_time += time_list.pop() + ", "
    time_list.reverse()
    readable_time += ": ".join(time_list)
    return readable_time


@routes.get("/status", allow_head=True)
async def status_handler(_: web.Request):
    return web.json_response(
        {
            "server_status": "running",
            "uptime": _get_readable_time(time.time() - StartTime),
            "version": __version__,
        }
    )


@routes.get("/watch", allow_head=True)
async def watch_handler(request: web.Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visuales Stream Player</title>
        <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #6366f1;
                --bg: #0f172a;
                --panel: #1e293b;
            }
            body {
                margin: 0; padding: 0;
                background-color: var(--bg);
                color: #f8fafc;
                font-family: 'Inter', sans-serif;
                display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                min-height: 100vh;
            }
            .container {
                width: 95%; max-width: 900px;
                background: var(--panel);
                padding: 1.5rem; border-radius: 16px;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            }
            h1 {
                text-align: center; margin: 0 0 1.5rem 0; font-size: 1.5rem;
                background: linear-gradient(45deg, #a855f7, #6366f1);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            }
            .video-container {
                width: 100%; border-radius: 12px; overflow: hidden;
                background: #000; aspect-ratio: 16 / 9;
                border: 1px solid #334155;
            }
            .video-js { width: 100%; height: 100%; }
            .vjs-big-play-button {
                top: 50% !important; left: 50% !important;
                transform: translate(-50%, -50%) !important;
                background-color: rgba(99, 102, 241, 0.8) !important;
                border-radius: 50% !important; width: 2em !important; height: 2em !important;
                line-height: 2em !important; border: none !important;
            }
            .input-box {
                margin-top: 1.5rem; display: flex; gap: 8px;
            }
            input {
                flex: 1; background: #0f172a; border: 1px solid #334155;
                color: white; padding: 10px 15px; border-radius: 8px; outline: none;
            }
            button {
                background: var(--primary); color: white; border: none;
                padding: 10px 20px; border-radius: 8px; cursor: pointer;
                font-weight: 600; transition: 0.2s;
            }
            button:hover { background: #4f46e5; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Visuales Stream Player</h1>
            <div class="video-container">
                <video id="player" class="video-js vjs-big-play-centered vjs-theme-city" controls preload="auto" data-setup='{}'>
                    <p class="vjs-no-js">Para ver este video, habilita JavaScript o usa un navegador compatible.</p>
                </video>
            </div>
            <div class="input-box">
                <input type="text" id="streamUrl" placeholder="Pega aquí tu enlace de stream...">
                <button onclick="loadVideo()">Cargar</button>
            </div>
        </div>
        <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
        <script>
            const player = videojs('player', {
                fluid: true,
                playbackRates: [0.5, 1, 1.5, 2],
                userActions: { hotkeys: true }
            });

            function loadVideo() {
                const urlInput = document.getElementById('streamUrl').value.trim();
                if (!urlInput) return;
                
                let finalUrl = urlInput;
                if (!finalUrl.includes('s=1')) {
                    finalUrl += finalUrl.includes('?') ? '&s=1' : '?s=1';
                }
                
                // Intentar detectar el tipo por la extensión en la URL
                let type = 'video/mp4';
                if (finalUrl.includes('.webm')) type = 'video/webm';
                if (finalUrl.includes('.ogg')) type = 'video/ogg';
                if (finalUrl.includes('.mkv')) type = 'video/x-matroska';

                player.src({ type: type, src: finalUrl });
                player.play().catch(e => console.log("Play error:", e));
            }

            window.onload = function() {
                const urlParams = new URLSearchParams(window.location.search);
                const streamUrl = urlParams.get('url');
                if (streamUrl) {
                    document.getElementById('streamUrl').value = streamUrl;
                    setTimeout(loadVideo, 500);
                }
            };
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type="text/html")



@routes.get(r"/stream/{messageID:\d+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        message_id = int(request.match_info["messageID"])
        secure_hash = request.rel_url.query.get("hash")
        logger.info(f"--- Recibida petición HTTP para /stream/{message_id} ---")
        return await media_streamer(request, message_id, secure_hash)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        return web.Response(status=204)
    except Exception as e:
        logger.critical(str(e), exc_info=True)
        raise web.HTTPInternalServerError(text=str(e))


async def media_streamer(request: web.Request, message_id: int, secure_hash: str):
    """Maneja el streaming de un archivo con soporte de Range requests."""
    head: bool = request.method == "HEAD"
    ip = _get_requester_ip(request)
    range_header = request.headers.get("Range", 0)

    if _streamer is None:
        return web.Response(status=503, text="Servidor de streaming no inicializado")

    logger.info(f"Petición de stream: ID={message_id} | IP={ip} | Range={range_header}")

    # Obtener propiedades del archivo
    file_info = await _streamer.get_file_properties(message_id)
    if not file_info:
        return web.Response(status=404, text="Archivo no encontrado")

    # Verificar hash de seguridad
    full_hash = pack_file(
        file_info.file_name,
        file_info.file_size,
        file_info.mime_type,
        file_info.message_id,
    )
    if get_short_hash(full_hash) != secure_hash:
        logger.debug("Hash inválido para message_id %s", message_id)
        return web.HTTPForbidden(text="Hash inválido")

    file_size = file_info.file_size

    # Parsear Range header
    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    until_bytes = min(until_bytes, file_size - 1)
    req_length = until_bytes - from_bytes + 1

    if not head:
        if not _allow_request(ip):
            return web.Response(status=429)
        _ongoing_requests[ip] += 1
        body = _streamer.download(file_info, file_size, from_bytes, until_bytes)
    else:
        body = None

    mime_type = file_info.mime_type
    file_name = file_info.file_name

    if not mime_type:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    disposition = "inline" if request.rel_url.query.get("s") else "attachment"

    headers = {
        "Content-Type": mime_type,
        "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
        "Content-Length": str(req_length),
        "Content-Disposition": f'{disposition}; filename="{file_name}"',
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Range, Content-Type",
        "Access-Control-Expose-Headers": "Content-Range, Content-Length, Accept-Ranges",
    }

    response = web.StreamResponse(
        status=206 if range_header or request.http_range.start is not None else 200,
        reason="Partial Content" if range_header else "OK",
        headers=headers,
    )

    await response.prepare(request)

    try:
        if body:
            async for chunk in body:
                await response.write(chunk)
    except (ConnectionResetError, ConnectionAbortedError):
        logger.info(f"Conexión cerrada por el cliente: {ip}")
    finally:
        _ongoing_requests[ip] -= 1

    return response



async def start_stream_server(client):
    """Inicia el servidor aiohttp de streaming."""
    init_streamer(client)

    app = web.Application(client_max_size=1024 * 8)
    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, StreamConfig.BIND_ADDRESS, StreamConfig.PORT).start()

    logger.info("Servidor de streaming iniciado en %s", StreamConfig.URL)
    return runner
