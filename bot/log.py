import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name="visuales_bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:

            c_handler = logging.StreamHandler()
            os.makedirs("logs", exist_ok=True)
            log_filename = f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"
            f_handler = logging.FileHandler(log_filename, encoding='utf-8')
            
            format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            c_format = logging.Formatter(format_str)
            f_format = logging.Formatter(format_str)
            c_handler.setFormatter(c_format)
            f_handler.setFormatter(f_format)
            
            self.logger.addHandler(c_handler)
            self.logger.addHandler(f_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def debug(self, message):
        self.logger.debug(message)

logger = Logger().logger
