from abc import ABC, abstractmethod
from typing import Tuple

class BaseProvider(ABC):
    """
    Clase base para todos los servicios de descarga (GDrive, YouTube)

    """
    
    @abstractmethod
    def matches(self, url: str) -> bool:
        """Determina si este provider puede manejar la URL dada."""
        pass

    @abstractmethod
    async def download(self, url: str, destination: str, task_key: str) -> Tuple[str, str]:
        """
        Descarga el archivo y retorna (file_path, filename).
        """
        pass
