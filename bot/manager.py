from typing import List, Optional
from bot.providers.base import BaseProvider
from bot.providers.gdrive import GDriveProvider
from bot.providers.ytdlp import YoutubeDLProvider
from bot.providers.uploadhaven import UploadHavenProvider


class DownloadManager:
    def __init__(self):
        self.providers: List[BaseProvider] = [
            GDriveProvider(),
            YoutubeDLProvider(),
            UploadHavenProvider(),
        ]
        def __new__(cls):
            if not hasattr(cls, '_instance'):
                cls._instance = super(DownloadManager, cls).__new__(cls)
            return cls._instance
            
    def get_provider(self, url: str) -> Optional[BaseProvider]:
        for provider in self.providers:
            if provider.matches(url):
                return provider
        return None

manager = DownloadManager()
