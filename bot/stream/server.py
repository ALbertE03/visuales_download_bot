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


@routes.get(r"/watch/{messageID:\d+}", allow_head=True)
async def watch_handler(request: web.Request):
    """Muestra una página HTML con reproductor de video."""
    try:
        message_id = int(request.match_info["messageID"])
        secure_hash = request.rel_url.query.get("hash")

        file_info = await _streamer.get_file_properties(message_id)
        if not file_info:
            return web.Response(status=404, text="Archivo no encontrado")

        # Verificar hash
        full_hash = pack_file(
            file_info.file_name,
            file_info.file_size,
            file_info.mime_type,
            file_info.message_id,
        )
        if get_short_hash(full_hash) != secure_hash:
            return web.HTTPForbidden(text="Hash inválido")

        stream_url = f"{StreamConfig.URL}stream/{message_id}?hash={secure_hash}"

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_info.file_name} - Visuales UCLV</title>
    <!-- Plyr CSS para estilos profesionales -->
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --bg-color: #0f1115;
            --card-bg: #1a1d24;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: var(--bg-color);
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            color: var(--text-main);
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            padding: 2rem 1rem;
        }}
        .header {{
            width: 100%;
            max-width: 1000px;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .header-title {{
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .container {{
            width: 100%;
            max-width: 1000px;
            background: var(--card-bg);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .video-wrapper {{
            position: relative;
            background: #000;
            width: 100%;
            aspect-ratio: 16/9;
        }}
        .plyr {{
            height: 100%;
            --plyr-color-main: var(--primary);
        }}
        .info-section {{
            padding: 1.5rem 2rem;
        }}
        .filename {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            word-break: break-word;
            line-height: 1.4;
        }}
        .meta-info {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
            display: flex;
            gap: 1rem;
            align-items: center;
        }}
        .meta-tag {{
            background: rgba(255,255,255,0.1);
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 0.8rem;
        }}
        .actions {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid transparent;
            cursor: pointer;
        }}
        .btn-primary {{
            background: var(--primary);
            color: white;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
        }}
        .btn-primary:hover {{ background: var(--primary-hover); transform: translateY(-1px); }}
        .btn-secondary {{
            background: rgba(255,255,255,0.05);
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .btn-secondary:hover {{ background: rgba(255,255,255,0.1); }}
        .btn svg {{ width: 18px; height: 18px; }}
        
        .controls-xtra {{
            margin-bottom: 1rem;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .custom-file-upload {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 6px;
            background: rgba(255,255,255,0.08);
            font-size: 0.85rem;
            transition: 0.2s;
            border: 1px dashed rgba(255,255,255,0.2);
            color: var(--text-muted);
        }}
        .custom-file-upload:hover {{
            background: rgba(255,255,255,0.12);
            color: #fff;
        }}
        input[type="file"] {{ display: none; }}
        
        #audio-track-selector {{
            display: none;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            padding: 8px;
            border-radius: 6px;
            font-size: 0.85rem;
            outline: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#gradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#3b82f6" />
                    <stop offset="100%" stop-color="#8b5cf6" />
                </linearGradient>
            </defs>
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span class="header-title">Stream</span>
    </div>

    <div class="container">
        <div class="video-wrapper">
            <video id="player" controls crossorigin playsinline>
                <source src="{stream_url}" type="{file_info.mime_type or 'video/mp4'}">
            </video>
        </div>
        
        <div class="info-section">
            <div class="filename">{file_info.file_name}</div>
            <div class="meta-info">
                <span class="meta-tag">{file_info.file_size / 1024 / 1024:.1f} MB</span>
                <span>•</span>
                <span>Streaming</span>
            </div>
            
            <div class="controls-xtra">
                <label class="custom-file-upload">
                    <input type="file" id="sub-upload" accept=".vtt,.srt" />
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    Añadir Subtítulo (.srt/.vtt)
                </label>
                <select id="audio-track-selector"></select>
            </div>

            <div class="actions">
                <a href="{stream_url}&s=1" class="btn btn-primary" download>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Descargar
                </a>
                <button class="btn btn-secondary" onclick="navigator.clipboard.writeText('{stream_url}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    Copiar Link
                </button>
                <a href="vlc://{stream_url}" class="btn btn-secondary" title="Abrir en VLC Media Player (Mejor para Dual Audio y formato MKV)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    Abrir en VLC
                </a>
            </div>
        </div>
    </div>

    <!-- Plyr JS -->
    <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const video = document.getElementById('player');
            const player = new Plyr(video, {{
                captions: {{ active: true, update: true, language: 'auto' }},
                i18n: {{
                    quality: 'Calidad',
                    speed: 'Velocidad',
                    captions: 'Subtítulos',
                    disabled: 'Desactivado',
                    enabled: 'Activado',
                }}
            }});

            // Manejo de subtítulos locales
            document.getElementById('sub-upload').addEventListener('change', function(e) {{
                const file = e.target.files[0];
                if (!file) return;

                const url = URL.createObjectURL(file);
                const track = document.createElement('track');
                track.kind = 'captions';
                track.label = file.name;
                track.srclang = 'es';
                track.src = url;
                track.default = true;

                Array.from(video.querySelectorAll('track')).forEach(t => t.remove());
                video.appendChild(track);
                
                alert(`Subtítulo "${{file.name}}" cargado correctamente. Puedes activarlo en el menú (CC).`);
                
                setTimeout(() => {{
                    track.mode = 'showing';
                }}, 500);
            }});

            // Soporte de Múltiples Pistas de Audio (Dual Audio) en la web
            video.addEventListener('loadedmetadata', () => {{
                const audioTracks = video.audioTracks;
                const selector = document.getElementById('audio-track-selector');
                if (audioTracks && audioTracks.length > 1) {{
                    selector.style.display = 'inline-flex';
                    selector.innerHTML = '';
                    for (let i = 0; i < audioTracks.length; i++) {{
                        const option = document.createElement('option');
                        option.value = i;
                        option.text = audioTracks[i].label || audioTracks[i].language || `Audio Track ${{i + 1}}`;
                        selector.appendChild(option);
                        
                        if (audioTracks[i].enabled) {{
                            option.selected = true;
                        }}
                    }}
                    
                    selector.addEventListener('change', (e) => {{
                        for (let i = 0; i < audioTracks.length; i++) {{
                            audioTracks[i].enabled = (i == parseInt(e.target.value));
                        }}
                    }});
                }}
            }});
        }});
    </script>
</body>
</html>"""

        return web.Response(text=html, content_type="text/html")

    except Exception as e:
        logger.error(f"Error en watch_handler: {e}")
        return web.Response(status=500, text="Error interno")


@routes.get(r"/stream/{messageID:\d+}", allow_head=True)
async def stream_handler(request: web.Request):
    try:
        message_id = int(request.match_info["messageID"])
        secure_hash = request.rel_url.query.get("hash")
        logger.info(f"--- Recibida petición HTTP para /stream/{message_id} ---")
        return await media_streamer(request, message_id, secure_hash)
    except (AttributeError, BadStatusLine, ConnectionResetError, ConnectionAbortedError, ConnectionError):
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

    # Forzar MIME type para videos si es necesario
    import os
    ext = os.path.splitext(file_name.lower())[1]
    video_mimes = {
        ".mp4": "video/mp4",
        ".m4v": "video/x-m4v",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo"
    }

    if ext in video_mimes:
        mime_type = video_mimes[ext]
    elif mime_type and "video" in mime_type:
        mime_type = "video/mp4"

    headers = {
        "Content-Type": mime_type,
        "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
        "Content-Length": str(req_length),
        "Content-Disposition": f'{disposition}; filename="{file_name}"',
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Connection": "keep-alive",
        "Cache-Control": "public, max-age=3600",
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
    except (ConnectionResetError, ConnectionAbortedError, ConnectionError):
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

    logger.info(f"Servidor de streaming iniciado en {StreamConfig.URL}")
    return runner
