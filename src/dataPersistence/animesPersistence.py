__author__ = "Jose David Escribano Orts"
__subsystem__ = "DataPersistence"
__module__ = "roadsPersistence"
__version__ = "1.0"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import json
import os

from APIs.animeflv.animeflv import AnimeInfo
from src.utils.db.sqlite import ServiceDB
from utils.utils import get_resource_path


class AnimesPersistence(ServiceDB):
    DB_NAME = "DB_Animes.db"

    _table_name: str = "ANIMES"
    _list_fields: list = ["id", "anime_id", "title", "poster_url", "synopsis", "genres", "episodes", "is_favourite", "is_watching",
                          "is_finished", "is_pending", "last_watched_episode"]
    _list_fields_type: list = ["INTEGER", "INTEGER", "VARCHAR(100)", "VARCHAR(100)", "TEXT", "JSON", "JSON", "BOOLEAN", "BOOLEAN", "BOOLEAN",
                               "BOOLEAN", "INTEGER"]
    _primary_key: str = "id AUTOINCREMENT"

    POS_ID: int = 0
    POS_ANIME_ID: int = 1
    POS_TITLE: int = 2
    POS_POSTER_URL: int = 3
    POS_SYNOPSIS: int = 4
    POS_GENRES: int = 5
    POS_EPISODES: int = 6
    POS_IS_FAVOURITE: int = 7
    POS_IS_WATCHING: int = 8
    POS_IS_FINISHED: int = 9
    POS_IS_PENDING: int = 10
    POS_LAST_WATCHED_EPISODE: int = 11

    def __init__(self):
        try:
            self.path_db = get_resource_path(f"resources/DB/{self.DB_NAME}")
            super().__init__(self.path_db)
        except Exception as e:
            print(f"Error al iniciar la base de datos {self.DB_NAME}: {e}")

    def start(self):
        try:
            if not os.path.isfile(self.path_db):
                if not self._create_db_animes():
                    raise Exception(f"Error al crear la base de datos {self.DB_NAME}")
        except Exception as e:
            print(f"Error al empezar la base de datos {self.DB_NAME}: {e}")

    def insert_anime(self, record: dict):
        if record is None:
            return False
        record[self._list_fields[self.POS_ID]] = "NULL"
        record[self._list_fields[self.POS_GENRES]] = json.dumps(record[self._list_fields[self.POS_GENRES]])
        record[self._list_fields[self.POS_EPISODES]] = json.dumps(record[self._list_fields[self.POS_EPISODES]][::-1])
        record.setdefault("last_watched_episode", 0)
        return self.insert_record_db(self._table_name, self._list_fields, record)

    def get_anime_by_anime_id(self, anime_id: int):
        sql: str = f"SELECT * FROM {self._table_name} WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_id}'"
        return self._db.query_sql(sql, tuple(), self._list_fields)

    def get_favourite_animes(self):
        sql: str = f"SELECT * FROM {self._table_name} WHERE {self._list_fields[self.POS_IS_FAVOURITE]} = True"
        return self._db.query_sql(sql, tuple(), self._list_fields)

    def get_watching_animes(self):
        sql: str = f"SELECT * FROM {self._table_name} WHERE {self._list_fields[self.POS_IS_WATCHING]} = True"
        return self._db.query_sql(sql, tuple(), self._list_fields)

    def get_pending_animes(self):
        sql: str = f"SELECT * FROM {self._table_name} WHERE {self._list_fields[self.POS_IS_PENDING]} = True"
        return self._db.query_sql(sql, tuple(), self._list_fields)

    def get_finished_animes(self):
        sql: str = f"SELECT * FROM {self._table_name} WHERE {self._list_fields[self.POS_IS_FINISHED]} = True"
        return self._db.query_sql(sql, tuple(), self._list_fields)

    def update_anime_to_favourite(self, anime_record: AnimeInfo):
        res, animes = self.get_anime_by_anime_id(anime_record.id)
        if not res:
            return False
        if len(animes) == 0:
            anime_record = {
                "anime_id": anime_record.id,
                "title": anime_record.title,
                "poster_url": anime_record.poster,
                "synopsis": anime_record.synopsis,
                "genres": anime_record.genres,
                "episodes": [episode.id for episode in anime_record.episodes],
                "is_favourite": True,
                "is_pending": False,
                "is_finished": False,
                "is_watching": False,
            }
            return self.insert_anime(anime_record)

        sql = f"UPDATE {self._table_name} SET is_favourite = 1 " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_record.id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_to_not_favourite(self, anime_id: int):
        sql = f"UPDATE {self._table_name} SET is_favourite = 0 " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_to_watching(self, anime_record: AnimeInfo):
        res, animes = self.get_anime_by_anime_id(anime_record.id)
        if not res:
            return False
        if len(animes) == 0:
            anime_record = {
                "anime_id": anime_record.id,
                "title": anime_record.title,
                "poster_url": anime_record.poster,
                "synopsis": anime_record.synopsis,
                "genres": anime_record.genres,
                "episodes": [episode.id for episode in anime_record.episodes],
                "is_watching": True,
                "is_favourite": False,
                "is_pending": False,
                "is_finished": False,
            }
            return self.insert_anime(anime_record)

        sql = f"UPDATE {self._table_name} SET is_watching = 1, is_finished = 0, is_pending = 0 " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_record.id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_to_not_watching(self, anime_id: int):
        res, anime = self.get_anime_by_anime_id(anime_id)
        if not res:
            return False
        is_pending = anime[0][self._list_fields[self.POS_IS_PENDING]]
        sql = f"UPDATE {self._table_name} SET is_watching = 0, is_pending = {is_pending} " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_to_pending(self, anime_record: AnimeInfo):
        res, animes = self.get_anime_by_anime_id(anime_record.id)
        if not res:
            return False
        if len(animes) == 0:
            anime_record = {
                "anime_id": anime_record.id,
                "title": anime_record.title,
                "poster_url": anime_record.poster,
                "synopsis": anime_record.synopsis,
                "genres": anime_record.genres,
                "episodes": [episode.id for episode in anime_record.episodes],
                "is_pending": True,
                "is_favourite": False,
                "is_finished": False,
                "is_watching": False,
            }
            return self.insert_anime(anime_record)

        sql = f"UPDATE {self._table_name} SET is_pending = 1, is_finished = 0, is_watching = 0 " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_record.id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_to_not_pending(self, anime_id: int):
        sql = f"UPDATE {self._table_name} SET is_pending = 0 " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_to_finished(self, anime_record: AnimeInfo):
        res, animes = self.get_anime_by_anime_id(anime_record.id)
        if not res:
            return False
        if len(animes) == 0:
            anime_record = {
                "anime_id": anime_record.id,
                "title": anime_record.title,
                "poster_url": anime_record.poster,
                "synopsis": anime_record.synopsis,
                "genres": anime_record.genres,
                "episodes": [episode.id for episode in anime_record.episodes],
                "is_finished": True,
                "is_favourite": False,
                "is_pending": False,
                "is_watching": False,
            }
            return self.insert_anime(anime_record)

        sql = f"UPDATE {self._table_name} SET is_finished = 1, is_pending = 0, is_watching = 0 " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_record.id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_to_not_finished(self, anime_id):
        res, anime = self.get_anime_by_anime_id(anime_id)
        if not res:
            return False
        is_watching = anime[0][self._list_fields[self.POS_IS_WATCHING]]
        sql = f"UPDATE {self._table_name} SET is_finished = 0, is_pending = 1, is_watching = {is_watching} " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_id}'"
        return self._db.update_sql(sql, tuple())

    def update_anime_episodes(self, anime_id, episodes: AnimeInfo.episodes):
        new_episodes_list = [episode.id for episode in episodes][::-1]
        sql = f"UPDATE {self._table_name} SET episodes = '{new_episodes_list}' " \
              f"WHERE {self._list_fields[self.POS_ANIME_ID]} = '{anime_id}'"
        return self._db.update_sql(sql, tuple())

    def _create_db_animes(self) -> bool:
        """
        Se encarga de crear db de sessions.
        """
        print(f"Creando base de datos {self.DB_NAME}")
        return self.create_table(self._table_name, self._list_fields, self._list_fields_type, self._primary_key)


class AnimesPersistenceSingleton:
    __instance = None

    def __new__(cls):
        if AnimesPersistenceSingleton.__instance is None:
            AnimesPersistenceSingleton.__instance = AnimesPersistence()
        return AnimesPersistenceSingleton.__instance