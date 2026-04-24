import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bot.core.mongodb import db
from bot.log import logger


class SearchEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words=None)
        self.titles = []
        self.msg_ids = []
        self.matrix = None
        self.is_fitted = False

    def refresh(self):
        """Recarga los datos de MongoDB y entrena el vectorizador"""
        movies = db.get_all_movies()
        if not movies:
            logger.warning("No hay películas en la base de datos para indexar.")
            return

        self.titles = [m["title"] for m in movies]
        self.msg_ids = [m["msg_id"] for m in movies]

        try:
            self.matrix = self.vectorizer.fit_transform(self.titles)
            self.is_fitted = True
            logger.info(
                f"Motor de búsqueda actualizado: {len(self.titles)} títulos indexados."
            )
        except Exception as e:
            logger.error(f"Error entrenando el motor de búsqueda: {e}")
            self.is_fitted = False

    def search(self, query, top_k=5):
        """Busca similitud de coseno para una query dada"""
        if not self.is_fitted or not self.titles:
            self.refresh()
            if not self.is_fitted:
                return []

        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.matrix).flatten()

            indices = np.argsort(similarities)[::-1][:top_k]

            results = []
            for i in indices:
                if similarities[i] > 0.5:
                    results.append(
                        {
                            "title": self.titles[i],
                            "msg_id": self.msg_ids[i],
                            "score": float(similarities[i]),
                        }
                    )
            return results
        except Exception as e:
            logger.error(f"Error en la búsqueda: {e}")
            return []


engine = SearchEngine()
