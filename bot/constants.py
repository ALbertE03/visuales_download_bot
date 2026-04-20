import os

class CONSTANTS:
    # Directorios y Bases de Datos
    DOWNLOAD_DIR = "downloads"
    DB_DIR = "bot/database"
    PROCESSED_DB = os.path.join(DB_DIR, "processed.json")
    EXPLORER_CACHE_DB = os.path.join(DB_DIR, "explorer_cache.json")
    
    # Formatos Soportados
    VIDEO_FORMATS = ('.mp4', '.mkv', '.avi', '.mpg', '.dat', '.wmv', '.mov', '.mpeg')
    
    # Mensajes de Telegram
    MSG_CMD_DOWNLOAD_USAGE = "Uso: /dl <url>"
    
    MSG_ANALYZING = "Analizando enlace..."
    MSG_DOWNLOADING = "Descargando..."
    MSG_UPLOADING = "Subiendo a Telegram..."
    MSG_INVALID_LINK = "Enlace no válido o no soportado."
    MSG_ERROR_OCCURRED = "Ocurrió un error: {error_msg}"
    
    # Mensajes de Comandos y Bot
    MSG_NO_PROVIDER = "No se encontró un proveedor para manejar esta URL."
    MSG_INVALID_MAGNET = "Enlace magnet inválido."
    MSG_INVALID_TORRENT_FILE = "Archivo .torrent inválido o no soportado."
    MSG_CHOOSE_OPTION = "Elige una opcion:"
    MSG_START_BUTTON = "Comenzar"
    MSG_SETTINGS_BUTTON = "Ajustes"
    
    MSG_HELP = (
        "Comandos disponibles:\n"
        " - /down <ruta> - Descarga desde Visuales UCLV\n"
        " - /yt <url> - Descarga desde YouTube\n"
        " - /ig <url> - Descarga desde Instagram\n"
        " - /tw <url> - Descarga desde Twitter (X)\n"
        " - /gdrive <url> - Descarga desde Google Drive\n"
        " - /torrent <magnet_link> - Descarga un torrent (Magnet)\n"
        " - También puedes enviar un archivo .torrent directamente.\n"
        " - /status - Panel de Control"
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
    
    # UI Panel
    PANEL_HEADER = "[ PANEL DE CONTROL ]\n"
    PANEL_TASK_HEADER = "== {task_type} =="
    PANEL_FILENAME = "Archivo: {filename}"
    PANEL_STATUS = "Estado: {status}"
    PANEL_SPEED = "Velocidad: {speed}"
    PANEL_ETA = "Restante: {eta}\n"
    PANEL_PROGRESS_BAR = "[{bar}] {progress:.1f}%"
    PANEL_COMPLETED = "Completados: {completed}"
    PANEL_FAILED = "Fallidos: {failed}"
    PANEL_QUEUE = "En Cola: {queue}"
    PANEL_DIVIDER = "-" * 15
    PANEL_UP_TO_DATE = "{downloaded} de {total}"
    
    # Mensajes de Log y otros
    LOG_DOWNLOADING = "Descargando {filename} desde {url}..."
    LOG_UPLOADING = "Subiendo {filename} ({size}) a {target}..."
    LOG_UPLOAD_SUCCESS = "Finalizado: {filename} enviado con exito."
    LOG_UPLOAD_RETRY = "Error subiendo {filename} (intento {attempt}): {error}. Reintentando..."
    LOG_SESSION_ERROR = "Error de sesion detectado en {filename}, esperando para reintentar..."
    LOG_FILE_DELETED = "Archivo local eliminado: {filename}"
    LOG_UPLOAD_ERROR = "Error subiendo {filename}: {error}"
    LOG_UPLOAD_WORKER_ERROR = "Error en worker de subida: {error}"
    LOG_STATUS_LOOP_ERROR = "Error en bucle de status: {error}"
    LOG_ERROR_DOWNLOADING = "Error descargando {filename}: {error}"
    MSG_ADDED_QUEUE = "Añadido a la cola: {filename}"
    MSG_ADDED_TORRENT_QUEUE = "Añadido a la cola de torrents."
    MSG_GET_TORRENT_FILE_OK = "Archivo .torrent descargado con éxito."
    MSG_GETTING_STATUS = "Obteniendo estado..."
    
    # Logs Adicionales
    LOG_TORRENT_START = "Iniciando descarga de torrent: {filename}"
    LOG_TORRENT_FINISHED = "Torrent {filename} descargado completamente."
    LOG_TORRENT_FOLDER = "Torrent {filename} es una carpeta, filtrando videos para subir..."
    LOG_TORRENT_METADATA_WAIT = "Esperando metadata..."
    LOG_TORRENT_METADATA_OK = "Metadata obtenida"
    LOG_TORRENT_EXITING = "Saliendo del worker de torrent..."
    LOG_SKIP_NON_VIDEO = "Omitiendo archivo no video: {file}"
    LOG_SKIP_TORRENT_NON_VIDEO = "Archivo torrent omitido por no ser video: {filename}"
    LOG_TORRENT_FILE_ERROR = "Error descargando archivo .torrent: {error}"
    LOG_DETECTED_DIR = "Detectado directorio en upload_file: {filename}, subiendo contenidos..."
    LOG_SPLITTING = "Archivo {filename} es mayor a 2GB, dividiendo..."
    
    # Mensajes de Error y Excepciones
    ERR_NO_GDRIVE_ID = "ID de Google Drive no encontrado."
    ERR_FILE_NOT_FOUND = "Error: El archivo no existe: {path}"
    
    # Tipos de Tareas (Keys)
    TASK_TYPE_DOWNLOAD = "download"
    TASK_TYPE_UPLOAD = "upload"
    TASK_TYPE_TORRENT = "torrent"
    #torrent 
    MSG_CMD_TORRENT_USAGE = "Uso: /torrent <magnet_link>"
    # Mensajes para Visuales UCLV
    MSG_CMD_VISUALES_USAGE = "Uso: /down <Path>"
    MSG_SEARCHING_VISUALES = "Buscando archivos en:\n{url}"
    MSG_CACHE_COMPLETE = "Caché completo cargado.\nAnadidos: {found}\nOmitidos: {skipped}"
    MSG_CACHE_PARTIAL = "Cache parcial: {found_total} archivos.\nBuscando el resto en la web..."
    MSG_SCAN_PARTIAL = "Escaneando parcial...\n({i}/{total} carpetas)\nEncontrados nuevos: {found}\nOmitidos/Cache: {skipped}"
    MSG_SEARCH_FINISHED = "Busqueda finalizada.\nNuevos: {found}\nTotal en carpeta: {total}"
    MSG_START_TRACKING = "Iniciating tracking..."
    MSG_START_TRACKING_CACHE = "Iniciating tracking (Cache)..."
    MSG_PROCESSING = "Procesando..."
    MSG_FINISHING = "Finalizando..."
    
    # Errores Adicionales
    ERR_NETWORK = "Error de red: El servidor respondio con error {status}"
    ERR_UNEXPECTED = "Error inesperado: {error}"
    ERR_FOLDER_SCAN = "Error en carpeta {url}: {error}"
    
    # Configuración de Descarga
    YDL_OPTS_DEFAULT = {
        "format": "bestvideo+bestaudio/best",
        "quiet": True,
        "no_warnings": True,
    }
    
    # Dominios soportados por yt-dlp
    YDL_SUPPORTED_DOMAINS = [
        'youtube.com', 'youtu.be', 'twitter.com', 'x.com', 
        'instagram.com', 'facebook.com', 'fb.watch', 'tiktok.com'
    ]
    
    # Google Drive Utility
    GDRIVE_API_URL = "https://docs.google.com/uc?export=download"
    
    # Configuración de Red y Transferencia
    LT_LISTEN_INTERFACES = "0.0.0.0:6881"
    CHUNK_SIZE = 8192 * 1024  # 8MB
    
    GDRIVE_PATTERNS = [
        r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/folderview\?id=([a-zA-Z0-9_-]+)',
    ]
