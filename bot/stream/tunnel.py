import subprocess
import re
import time
import logging
import threading

logger = logging.getLogger(__name__)


class CloudflareTunnel:
    def __init__(self, port: int):
        self.port = port
        self.url = None
        self._process = None
        self._stop_event = threading.Event()

    def start(self):
        """Inicia el túnel de Cloudflare y extrae la URL."""
        logger.info(f"Iniciando túnel de Cloudflare para el puerto {self.port}...")

        # Ejecutamos cloudflared tunnel --url http://localhost:PORT
        cmd = [
            "cloudflared",
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
