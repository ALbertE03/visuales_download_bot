import streamlit as st


class StreamConfig:
    """Configuración del servidor de streaming."""

    PORT: int = int(st.secrets.get("STREAM_PORT", 8080))
    BIND_ADDRESS: str = st.secrets.get("STREAM_BIND", "0.0.0.0")
    BIN_CHANNEL: int = int(st.secrets.get("STREAM_BIN_CHANNEL", "-1003726563984"))
    HASH_LENGTH: int = int(st.secrets.get("STREAM_HASH_LENGTH", 6))
    CHUNK_SIZE: int = 1024 * 1024
    CACHE_SIZE: int = 128
    REQUEST_LIMIT: int = 5

    # URL base del servidor de streaming
    _url = st.secrets.get("STREAM_URL", "")
    URL = _url.rstrip("/") + "/" if _url else f"http://{BIND_ADDRESS}:{PORT}/"

    @classmethod
    def update_url(cls, new_url: str):
        """Actualiza la URL pública (usado por el túnel)."""
        cls.URL = new_url.rstrip("/") + "/"
