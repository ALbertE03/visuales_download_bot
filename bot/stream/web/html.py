from bot.stream.file_properties import FileInfo
from bot.stream.web.styles import styles
from bot.stream.web.js import scripts

def create_html(file_info:FileInfo,stream_url:str)->str: 
    return f"""<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{file_info.file_name} - Visuales Stream</title>
        <!-- Plyr CSS -->
        <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
        <!-- Font -->
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        {styles()}
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
        {scripts()}
    </body>
    </html>"""
