import os
import certifi
from pymongo import MongoClient
from bot.log import logger
from pymongo.server_api import ServerApi

class MongoDB:
    def __init__(self):
        uri = os.getenv("MONGO_URI")

        if not uri:
            logger.error("No se encontró MONGO_URI en el archivo .env")
            self.client = None
            return

        try:
            ca = certifi.where()
            self.client = MongoClient(
                uri, 
                tlsCAFile=ca, 
                tlsAllowInvalidCertificates=True, 
                tls=True,
                server_api=ServerApi("1")
            )
            self.db = self.client["visuales_bot"]
            self.movies = self.db["movies"]
            self.settings = self.db["settings"]
            self.client.admin.command("ping")
            logger.info("Conexión exitosa a MongoDB")
        except Exception as e:
            logger.error(f"Error conectando a MongoDB: {e}")
            self.client = None

    def save_movie(self, movie_data):
        if not self.client:
            return
        try:
            self.movies.update_one(
                {"msg_id": movie_data["msg_id"]}, {"$set": movie_data}, upsert=True
            )
        except Exception as e:
            logger.error(f"Error guardando película en MongoDB: {e}")

    def get_all_movies(self):
        if not self.client:
            return []
        return list(self.movies.find({}, {"title": 1, "msg_id": 1}))

    def get_last_scanned_id(self, channel_id):
        if not self.client:
            return 0
        res = self.settings.find_one({"key": f"last_id_{channel_id}"})
        return res["value"] if res else 0

    def set_last_scanned_id(self, channel_id, last_id):
        if not self.client:
            return
        self.settings.update_one(
            {"key": f"last_id_{channel_id}"}, {"$set": {"value": last_id}}, upsert=True
        )


db = MongoDB()
