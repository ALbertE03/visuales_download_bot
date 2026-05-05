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
    <title>{file_info.file_name} - Visuales Stream</title>
    <!-- Plyr CSS -->
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <!-- 2026 Modern Font -->
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --bg-color: #030305;
            --panel-bg: rgba(20, 20, 25, 0.7);
            --panel-border: rgba(255, 255, 255, 0.06);
            --text-main: #ffffff;
            --text-muted: #a1a1aa;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 10% 0%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 100%, rgba(168, 85, 247, 0.1) 0%, transparent 40%);
            background-attachment: fixed;
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 3rem 1.5rem;
            -webkit-font-smoothing: antialiased;
        }}
        .header {{
            width: 100%;
            max-width: 1200px;
            margin-bottom: 2.5rem;
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .brand-icon {{
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 24px var(--primary-glow);
        }}
        .header-title {{
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #fff, #d4d4d8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .player-card {{
            width: 100%;
            max-width: 1200px;
            background: var(--panel-bg);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--panel-border);
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 30px 60px -15px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.03);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .video-wrapper {{
            background: #000;
            width: 100%;
            aspect-ratio: 16/9;
            position: relative;
        }}
        .plyr {{
            height: 100%;
            --plyr-color-main: var(--primary);
            --plyr-video-background: transparent;
            --plyr-control-radius: 8px;
        }}
        .info-panel {{
            padding: 2rem 2.5rem;
        }}
        .title-group {{
            margin-bottom: 1.5rem;
        }}
        .filename {{
            font-size: 1.4rem;
            font-weight: 600;
            line-height: 1.4;
            color: #fff;
            margin-bottom: 0.8rem;
            word-break: break-word;
        }}
        .tags {{
            display: flex;
            gap: 0.75rem;
            align-items: center;
            flex-wrap: wrap;
        }}
        .badge {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-muted);
            letter-spacing: 0.01em;
        }}
        .badge-live {{
            background: rgba(99, 102, 241, 0.1);
            color: #818cf8;
            border-color: rgba(99, 102, 241, 0.2);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .badge-live::before {{
            content: '';
            width: 6px;
            height: 6px;
            background: #818cf8;
            border-radius: 50%;
            box-shadow: 0 0 8px #818cf8;
        }}
        .controls-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--panel-border);
        }}
        .tools {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 12px;
            font-size: 0.95rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            cursor: pointer;
            border: none;
            user-select: none;
            outline: none;
        }}
        .btn-glow {{
            background: linear-gradient(135deg, var(--primary), #8b5cf6);
            color: white;
            box-shadow: 0 4px 15px var(--primary-glow), inset 0 1px 0 rgba(255,255,255,0.2);
        }}
        .btn-glow:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6), inset 0 1px 0 rgba(255,255,255,0.2);
            filter: brightness(1.1);
        }}
        .btn-glow:active {{
            transform: translateY(0);
        }}
        .btn-glass {{
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-main);
            border: 1px solid var(--panel-border);
        }}
        .btn-glass:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-1px);
        }}
        .btn svg {{ width: 18px; height: 18px; }}
        
        input[type="file"] {{ display: none; }}
        
        select.btn-glass {{
            appearance: none;
            padding-right: 36px;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='rgba(255,255,255,0.6)'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 16px;
            cursor: pointer;
        }}
        select.btn-glass:focus {{
            border-color: rgba(255,255,255,0.2);
            background-color: rgba(255,255,255,0.06);
        }}
        select option {{
            background: #18181b;
            color: #fff;
        }}
        
        @media (max-width: 768px) {{
            .info-panel {{ padding: 1.5rem; }}
            .filename {{ font-size: 1.25rem; }}
            body {{ padding: 1.5rem 1rem; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
        </div>
        <span class="header-title">Stream</span>
    </div>

    <div class="player-card">
        <div class="video-wrapper">
            <video id="player" controls crossorigin playsinline>
                <source src="{stream_url}" type="{file_info.mime_type or 'video/mp4'}">
            </video>
        </div>
        
        <div class="info-panel">
            <div class="title-group">
                <div class="filename">{file_info.file_name}</div>
                <div class="tags">
                    <span class="badge badge-live">Stream Activo</span>
                    <span class="badge">{file_info.file_size / 1024 / 1024:.1f} MB</span>
                    <span class="badge" style="text-transform: uppercase">{file_info.file_name.split('.')[-1].lower() if '.' in file_info.file_name else 'VIDEO'}</span>
                </div>
            </div>
            
            <div class="controls-row">
                <div class="tools">
                    <label class="btn btn-glass">
                        <input type="file" id="sub-upload" accept=".vtt,.srt" />
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        Añadir Subtítulo
                    </label>
                    <select id="audio-track-selector" class="btn btn-glass" style="display: none;"></select>
                </div>

                <div class="tools">
                    <a href="{stream_url}&s=1" class="btn btn-glow" download>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Descargar
                    </a>
                </div>
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
                
                // Animación de éxito
                const label = this.parentElement;
                const originalText = label.innerHTML;
                label.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Cargado con éxito`;
                label.style.borderColor = '#4ade80';
                label.style.color = '#4ade80';
                
                setTimeout(() => {{
                    track.mode = 'showing';
                    setTimeout(() => {{
                        label.innerHTML = originalText;
                        label.style.borderColor = '';
                        label.style.color = '';
                    }}, 3000);
                }}, 500);
            }});

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
