import subprocess
import re
import time
import logging
import threading
import os
import platform
import urllib.request
import stat

logger = logging.getLogger(__name__)


class CloudflareTunnel:
    def __init__(self, port: int):
        self.port = port
        self.url = None
        self._process = None
        self._stop_event = threading.Event()
        self.bin_path = self._get_bin_path()

    def _get_bin_path(self):
        """Determina la ruta del binario y lo descarga si es necesario."""
        local_bin = os.path.join(os.getcwd(), "bin", "cloudflared")
        
        # Si ya existe en la carpeta local, usar ese
        if os.path.exists(local_bin):
            return local_bin
            
        # Verificar si está instalado en el sistema
        try:
            subprocess.check_call(["cloudflared", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "cloudflared"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        # Si no está, descargarlo (especialmente para Streamlit Cloud)
        os.makedirs(os.path.dirname(local_bin), exist_ok=True)
        
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Mapeo de arquitecturas para los binarios de Cloudflare
        # https://github.com/cloudflare/cloudflared/releases
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
        
        if system == "linux":
            if "arm64" in machine or "aarch64" in machine:
                url += "cloudflared-linux-arm64"
            elif "arm" in machine:
                url += "cloudflared-linux-arm"
            else:
                url += "cloudflared-linux-amd64"
        elif system == "darwin": # Mac
            url += "cloudflared-darwin-amd64"
        else:
            return "cloudflared" # Revertir al default y esperar lo mejor

        logger.info(f"Descargando cloudflared desde {url}...")
        try:
            urllib.request.urlretrieve(url, local_bin)
            # Dar permisos de ejecución
            st = os.stat(local_bin)
            os.chmod(local_bin, st.st_mode | stat.S_IEXEC)
            logger.info("cloudflared descargado con éxito")
            return local_bin
        except Exception as e:
            logger.error(f"Error descargando cloudflared: {e}")
            return "cloudflared"

    def start(self):
        """Inicia el túnel de Cloudflare y extrae la URL."""
        logger.info(f"Iniciando túnel de Cloudflare para el puerto {self.port}...")

        cmd = [
            self.bin_path,
            "tunnel",
            "--url",
            f"http://127.0.0.1:{self.port}",
            "--no-autoupdate",
        ]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            logger.error(
                "No se encontró el binario 'cloudflared'. Asegúrate de que esté en packages.txt"
            )
            return None

        start_time = time.time()
        timeout = 30

        while time.time() - start_time < timeout:
            line = self._process.stdout.readline()
            if not line:
                break

            # Buscamos el patrón: https://*.trycloudflare.com
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                self.url = match.group(0)
                logger.info(f"¡Túnel creado con éxito! URL pública: {self.url}")
                # Iniciamos un hilo para que el proceso siga corriendo sin bloquear
                threading.Thread(target=self._monitor_tunnel, daemon=True).start()
                return self.url

            if "error" in line.lower():
                logger.error(f"Error de Cloudflare: {line.strip()}")

        logger.error("Tiempo de espera agotado buscando la URL del túnel")
        self.stop()
        return None

    def _monitor_tunnel(self):
        """Mantiene el proceso vivo y loguea errores."""
        while self._process and self._process.poll() is None:
            line = self._process.stdout.readline()
            if not line:
                break

            logger.debug(f"Cloudflare: {line.strip()}")

        if self._process:
            return_code = self._process.poll()
            logger.warning(f"El proceso del túnel terminó con código: {return_code}")

    def stop(self):
        """Detiene el túnel."""
        if self._process:
            self._process.terminate()
            self._process = None
            logger.info("Túnel de Cloudflare detenido")


def start_cloudflare_tunnel(port: int):
    tunnel = CloudflareTunnel(port)
    url = tunnel.start()
    return url, tunnel
