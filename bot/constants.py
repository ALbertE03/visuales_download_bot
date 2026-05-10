import os


class CONSTANTS:
    # Directorios y Bases de Datos
    DOWNLOAD_DIR = "downloads"
    DB_DIR = "database"
    PROCESSED_DB = os.path.join(DB_DIR, "processed.json")
    EXPLORER_CACHE_DB = os.path.join(DB_DIR, "explorer_cache.json")

    # Formatos Soportados
    VIDEO_FORMATS = (".mp4", ".mkv", ".avi", ".mpg", ".dat", ".wmv", ".mov", ".mpeg")

    # Mensajes de Telegram
    MSG_CMD_DOWNLOAD_USAGE = (
        "<blockquote><b>[i] Uso:</b> <code>/dl &lt;url&gt;</code></blockquote>"
    )

    MSG_ANALYZING = "<blockquote>[~] <i>Analizando enlace...</i></blockquote>"
    MSG_DOWNLOADING = "<blockquote>[~] <i>Descargando contenido...</i></blockquote>"
    MSG_UPLOADING = "<blockquote>[^] <i>Subiendo a Telegram...</i></blockquote>"
    MSG_INVALID_LINK = (
        "<blockquote><b>[x] Error:</b> Enlace no válido o no soportado.</blockquote>"
    )
    MSG_ERROR_OCCURRED = (
        "<blockquote><b>[x] Excepción no controlada:</b>\n<pre>{error_msg}</pre></blockquote>"
    )

    # Mensajes de Comandos y Bot
    MSG_NO_PROVIDER = "<blockquote><b>[!] Aviso:</b> No se encontró un administrador para manejar este enlace.</blockquote>"
    MSG_INVALID_MAGNET = (
        "<blockquote><b>[x] Error:</b> Enlace magnet o hash corrupto.</blockquote>"
    )
    MSG_INVALID_TORRENT_FILE = "<blockquote><b>[x] Error:</b> Archivo .torrent corrompido o ilegible.</blockquote>"
    MSG_CHOOSE_OPTION = "<blockquote><b>Opciones principales:</b></blockquote>"
    MSG_START_BUTTON = "Comenzar"
    MSG_SETTINGS_BUTTON = "Ajustes"

    MSG_HELP = (
        "<b>-- Descargas y Extracción --</b>\n"
        "<blockquote>"
        "<code>/down &lt;ruta&gt;</code> - Descargas directas desde Visuales UCLV.\n"
        "<code>/dl &lt;url&gt;</code> - Youtube, Mediafire, Google Drive, Instagram, X.\n"
        "<code>/torrent &lt;magnet&gt;</code> - Protocolo BitTorrent (con soporte de video).\n"
        "</blockquote>\n"
        "<b>-- Opciones de Medios --</b>\n"
        "<blockquote>"
        "<code>/stream</code> - Genera un enlace cifrado web para ver videos online.\n"
        "<code>/add</code> - Habilita la recolección de archivos para armar un ZIP.\n"
        "<code>/end</code> - Comprime recolección activa y envía a Telegram.\n"
        "</blockquote>\n"
        "<b>-- Monitor del Sistema --</b>\n"
        "<blockquote>"
        "<code>/status</code> - Abre el Panel de Control en tiempo real.\n"
        "<code>/server_status</code> - Estado de hardware y recursos.\n"
        "<code>/cancel</code> - Administra y detiene tareas activas."
        "</blockquote>\n"
        "<i>* Puedes enviar archivos .torrent como mensaje directo.</i>"
    )

    # Mensajes de Estado en Panel
    STATUS_WAITING = "Esperando para iniciar tareas..."
    STATUS_NO_TASKS = "Sin tareas activas en este momento."
    STATUS_CALCULATING = "calculando..."
    STATUS_METADATA = "Recopilando información (Metadata)..."
    STATUS_DOWN_TORRENT = "Descargando archivo Torrent..."

    TYPE_DOWNLOAD = "DESCARGANDO"
    TYPE_UPLOAD = "SUBIENDO"
    TYPE_TORRENT = "TORRENT"
    TYPE_GENERIC = "TAREA"
    MAX_VISIBLE_TASKS = 10
    # UI Panel
    PANEL_HEADER = "<b>=== PANEL DE CONTROL DEL SISTEMA ===</b>\n"
    PANEL_ACTIVE_TASKS_HEADER = "<b>| TAREAS ACTIVAS ({active_count})</b>"
    PANEL_NO_TASKS = "<blockquote><i>[-] Sistema en reposo. Esperando nuevas peticiones.</i></blockquote>\n"
    PANEL_TASK_ITEM = "<blockquote><b>{task_type}</b>: <code>{filename}</code>\n<b>[{bar}]</b> <code>{progress:.1f}%</code>\n<b>Transf:</b> <code>{downloaded}</code> / <code>{total}</code>\n<b>Ritmo:</b>  <code>{speed}</code> | <b>Fin:</b> <code>{eta}</code></blockquote>"
    PANEL_GLOBAL_HEADER = "<b>| METRICAS GLOBALES</b>"
    PANEL_GLOBAL_STATS = "<blockquote><b>Uptime:</b> <code>{uptime}</code>\n<b>Éxitos:</b> <code>{completed}</code> | <b>Fallos:</b> <code>{failed}</code></blockquote>"

    # Mensajes de Log y otros (Consola)
    LOG_DOWNLOADING = "Descargando {filename} desde {url}..."
    LOG_UPLOADING = "Subiendo {filename} ({size}) a {target}..."
    LOG_UPLOAD_SUCCESS = "Finalizado: {filename} enviado con exito."
    LOG_UPLOAD_RETRY = (
        "Error subiendo {filename} (intento {attempt}): {error}. Reintentando..."
    )
    LOG_SESSION_ERROR = (
        "Error de sesion detectado en {filename}, esperando para reintentar..."
    )
    LOG_FILE_DELETED = "Archivo local eliminado: {filename}"
    LOG_UPLOAD_ERROR = "Error subiendo {filename}: {error}"
    LOG_UPLOAD_WORKER_ERROR = "Error en worker de subida: {error}"
    LOG_STATUS_LOOP_ERROR = "Error en bucle de status: {error}"
    LOG_ERROR_DOWNLOADING = "Error descargando {filename}: {error}"

    # Avisos en Chat sobre Cola (Con formato blockquote)
    MSG_ADDED_QUEUE = "<blockquote><b>Aviso:</b> <code>{filename}</code> fue añadido a la cola.</blockquote>"
    MSG_ADDED_TORRENT_QUEUE = (
        "<blockquote><b>Aviso:</b> Añadido a la cola de torrents.</blockquote>"
    )
    MSG_GET_TORRENT_FILE_OK = (
        "<blockquote><b>Éxito:</b> Archivo .torrent procesado.</blockquote>"
    )
    MSG_GETTING_STATUS = "<i>Actualizando estado...</i>"

    # Logs Adicionales (Consola)
    LOG_TORRENT_START = "Iniciando descarga de torrent: {filename}"
    LOG_TORRENT_FINISHED = "Torrent {filename} descargado completamente."
    LOG_TORRENT_FOLDER = (
        "Torrent {filename} es una carpeta, preparando para subir contenidos..."
    )
    LOG_TORRENT_METADATA_WAIT = "Esperando metadata..."
    LOG_TORRENT_METADATA_TIMEOUT = (
        "Tiempo de espera de metadata agotado para: {filename}"
    )
    LOG_TORRENT_METADATA_OK = "Metadata obtenida"
    LOG_TORRENT_EXITING = "Saliendo del worker de torrent..."
    LOG_SKIP_NON_VIDEO = "Omitiendo archivo no video: {file}"
    LOG_SKIP_TORRENT_NON_VIDEO = "Archivo torrent omitido por no ser video: {filename}"
    LOG_TORRENT_FILE_ERROR = "Error descargando archivo .torrent: {error}"
    LOG_DETECTED_DIR = (
        "Detectado directorio en upload_file: {filename}, subiendo contenidos..."
    )
    LOG_SPLITTING = "Archivo {filename} es mayor a 2GB, dividiendo..."

    MSG_TORRENT_CANCELLED_NO_SEEDS = "<blockquote><b>[!] Abortando:</b> Descarga de torrent <code>{filename}</code> cancelada por falta de semillas.</blockquote>"

    # Mensajes de Error y Excepciones
    ERR_NO_GDRIVE_ID = (
        "<blockquote><b>Error:</b> ID de Google Drive no encontrado.</blockquote>"
    )
    ERR_FILE_NOT_FOUND = "<blockquote><b>Error:</b> El archivo no existe: <code>{path}</code></blockquote>"

    # Tipos de Tareas (Keys)
    TASK_TYPE_DOWNLOAD = "download"
    TASK_TYPE_UPLOAD = "upload"
    TASK_TYPE_TORRENT = "torrent"

    # torrent
    MSG_CMD_TORRENT_USAGE = (
        "<blockquote><b>Uso:</b> <code>/torrent &lt;magnet_link&gt;</code></blockquote>"
    )

    # Mensajes para Visuales UCLV
    MSG_CMD_VISUALES_USAGE = "<blockquote><b>Uso:</b> <code>/down &lt;ruta_en_el_servidor&gt;</code></blockquote>"
    MSG_SEARCHING_VISUALES = (
        "<b>Buscando archivos en:</b>\n<blockquote><code>{url}</code></blockquote>"
    )
    MSG_CACHE_COMPLETE = "<blockquote><b>Caché completo cargado.</b>\n<b>Añadidos:</b> <code>{found}</code>\n<b>Omitidos:</b> <code>{skipped}</code></blockquote>"
    MSG_CACHE_PARTIAL = "<blockquote><b>Caché parcial:</b> <code>{found_total}</code> archivos.</blockquote>\n<i>Buscando el resto en la web...</i>"
    MSG_SCAN_PARTIAL = "<blockquote><b>Escaneando carpetas:</b>\n<code>({i}/{total})</code> carpetas procesadas.\n<b>Nuevos:</b> <code>{found}</code>\n<b>Omitidos:</b> <code>{skipped}</code></blockquote>"
    MSG_SEARCH_FINISHED = "<blockquote><b>Búsqueda finalizada.</b>\n<b>Nuevos a descargar:</b> <code>{found}</code>\n<b>Total en carpeta:</b> <code>{total}</code></blockquote>"
    MSG_START_TRACKING = "<i>Iniciando rastreador...</i>"
    MSG_START_TRACKING_CACHE = "<i>Iniciando rastreador (Caché)...</i>"
    MSG_PROCESSING = "<i>Procesando datos...</i>"
    MSG_FINISHING = "<i>Finalizando operaciones...</i>"

    # Mensajes de Colección (Recolección)
    MSG_COLLECTION_ALREADY_ACTIVE = "<blockquote><b>[!] Aviso:</b> Ya tienes una recolección en curso. Envía <code>/end</code> para terminarla.</blockquote>"
    MSG_COLLECTION_STARTED = (
        "<b>[ MODO RECOLECCION ]</b>\n"
        "<blockquote>Envía <b>documentos</b>, <b>audios</b> o <b>videos</b> y los iré guardando para armar un paquete.\n"
        "Cuando termines, lanza el comando <code>/end</code>.</blockquote>\n"
        "<i>* Los mensajes de texto serán ignorados.</i>"
    )
    MSG_COLLECTION_NOT_ACTIVE = "<blockquote><b>[!] Negado:</b> No hay sesión de recolección. Usa <code>/add</code> para iniciar.</blockquote>"
    MSG_COLLECTION_EMPTY = "<blockquote><b>[i] Aviso:</b> Terminó la recolección, pero no enviaste nada.</blockquote>"
    MSG_COLLECTION_START_PACKING = "<blockquote><b>[*] Empaquetando</b> <code>{count}</code> <b>archivos...</b>\n\n<i>Paso 1. Solicitando copias temporales...</i></blockquote>"
    MSG_COLLECTION_DOWNLOADING = "<blockquote>[~] Descargando localmente <code>{idx}</code> de <code>{total}</code>...</blockquote>"
    MSG_COLLECTION_DOWNLOAD_ERROR = "<blockquote><b>[x] Error fatal:</b> Ningún archivo se pudo descargar al server para comprimir.</blockquote>"
    MSG_COLLECTION_COMPRESSING = "<blockquote><b>[#] Comprimiendo</b> <code>{count}</code> <b>archivos en .zip</b>\n<i>Usando nivel de fuerza bruta (9)</i></blockquote>"
    MSG_COLLECTION_ZIP_ERROR = "<blockquote><b>[x] Error:</b> Desbordamiento al instanciar binario zip.</blockquote>"
    MSG_COLLECTION_UPLOAD_QUEUE = "<blockquote><b>[*] Archivo finalizado:</b> El empaquetado pasó a la cola de subidas global.</blockquote>"
    MSG_COLLECTION_FILE_ADDED = "<blockquote><b>[+] Añadido a la bolsa virtual:</b> <code>{count}</code> items.</blockquote>"
    MSG_COLLECTION_CANCELLED = (
        "<blockquote><b>[x] Sistema Abortado.</b>\n"
        "Has enviado un formato de texto largo o no permitido. Reinicia con /add para intentar nuevamente.</blockquote>"
    )

    # Errores Adicionales
    ERR_NETWORK = "<blockquote><b>[x] Error de red perimetral:</b> El servidor respondió con status <code>{status}</code></blockquote>"
    ERR_UNEXPECTED = (
        "<blockquote><b>[!] Error interno:</b>\n<pre>{error}</pre></blockquote>"
    )
    ERR_FOLDER_SCAN = "<blockquote><b>[x] Error explorando</b> <code>{url}</code>:\n<pre>{error}</pre></blockquote>"

    # Configuración de Descarga
    YDL_OPTS_DEFAULT = {
        "format": "bestvideo+bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
    }

    # Dominios soportados por yt-dlp
    YDL_SUPPORTED_DOMAINS = [
        "youtube.com",
        "youtu.be",
        "twitter.com",
        "x.com",
        "instagram.com",
        "facebook.com",
        "fb.watch",
        "tiktok.com",
    ]

    # Google Drive Utility
    GDRIVE_API_URL = "https://docs.google.com/uc?export=download"

    # Configuración de Red y Transferencia
    LT_LISTEN_INTERFACES = "0.0.0.0:6881"
    CHUNK_SIZE = 8192 * 1024  # 8MB

    GDRIVE_PATTERNS = [
        r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/folderview\?id=([a-zA-Z0-9_-]+)",
    ]

    #  Configuraciones Técnicas y Límites 
    MAX_TG_SIZE: int = 2000 * 1024 * 1024  # 2GB límite de subida a Telegram
    SPLIT_SIZE_MB: int = 1990  # Tamaño en MB para picar archivos grandes
    DOWNLOAD_TIMEOUT: int = 120  # Timeout en segundos para peticiones HTTP
    QUEUE_TIMEOUT: int = 5  # Timeout en cola de espera
    TORRENT_TIMEOUT_NO_SEEDS: int = 1800  # 30 minutos sin recibir datos para cancelar torrent
    TORRENT_INIT_TIMEOUT: int = 300  # 5 minutos para obtener metadata del torrent
    DEFAULT_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
