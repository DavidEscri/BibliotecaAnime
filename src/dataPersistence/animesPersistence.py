__author__ = "Jose David Escribano Orts"
__subsystem__ = "DataPersistence"
__module__ = "animesPersistence"
__version__ = "2.0"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any

from APIs.common.models import AnimeInfo, AnimeGenreFilter, AnimeOrderFilter, EpisodeInfo
from utils.db.sqlite import ServiceDB
from utils.utils import get_resource_path


# ---------------------------------------------------------------------------
# Enums de dominio
# ---------------------------------------------------------------------------
class AnimeStatus(Enum):
    FAVOURITE = "is_favourite"
    WATCHING  = "is_watching"
    FINISHED  = "is_finished"
    PENDING   = "is_pending"


class AnimeField(Enum):
    """Define las columnas de la tabla ANIMES junto con su tipo SQLite.

    Cada miembro expone dos propiedades:
      - ``column``   → nombre de la columna en la BD.
      - ``sql_type`` → tipo SQLite usado al crear la tabla.
    """
    ID                   = ("id",                   "INTEGER")
    ANIME_ID             = ("anime_id",             "VARCHAR(100)")
    TITLE                = ("title",                "VARCHAR(100)")
    POSTER_URL           = ("poster_url",           "VARCHAR(200)")
    SYNOPSIS             = ("synopsis",             "TEXT")
    GENRES               = ("genres",               "JSON")
    EPISODES             = ("episodes",             "JSON")
    WATCHED_EPISODES     = ("watched_episodes",     "JSON")
    LAST_WATCHED_EPISODE = ("last_watched_episode", "INTEGER")
    IS_FAVOURITE         = ("is_favourite",         "BOOLEAN")
    IS_WATCHING          = ("is_watching",          "BOOLEAN")
    IS_FINISHED          = ("is_finished",          "BOOLEAN")
    IS_PENDING           = ("is_pending",           "BOOLEAN")

    @property
    def column(self) -> str:
        return self.value[0]

    @property
    def sql_type(self) -> str:
        return self.value[1]


# ---------------------------------------------------------------------------
# Dataclass de registro
# ---------------------------------------------------------------------------
@dataclass
class AnimeRecord:
    """Representación tipada de una fila de la tabla ANIMES.

    Los campos ``genres``, ``episodes`` y ``watched_episodes`` se almacenan
    como JSON en la BD y se deserializan automáticamente al construir la
    instancia desde ``from_db_dict``.
    """
    anime_id:             str
    title:                str
    poster_url:           str
    synopsis:             Optional[str]  = None
    genres:               List[str]      = field(default_factory=list)
    episodes:             List[int]      = field(default_factory=list)
    watched_episodes:     Set[int]       = field(default_factory=set)
    last_watched_episode: int            = 0
    is_favourite:         bool           = False
    is_watching:          bool           = False
    is_finished:          bool           = False
    is_pending:           bool           = False
    id:                   Optional[int]  = None  # autoincrement → None en inserción

    # ------------------------------------------------------------------
    # Serialización hacia la BD
    # ------------------------------------------------------------------
    def to_db_dict(self) -> Dict[str, Any]:
        """Convierte el record a un diccionario listo para insertar en SQLite."""
        episodes_reversed = list(reversed(self.episodes))
        watched_ranges    = AnimeRecord._episodes_to_ranges(self.watched_episodes)
        return {
            AnimeField.ID.column:                   "NULL",
            AnimeField.ANIME_ID.column:             self.anime_id,
            AnimeField.TITLE.column:                self.title,
            AnimeField.POSTER_URL.column:           self.poster_url,
            AnimeField.SYNOPSIS.column:             self.synopsis,
            AnimeField.GENRES.column:               json.dumps(self.genres),
            AnimeField.EPISODES.column:             json.dumps(episodes_reversed),
            AnimeField.WATCHED_EPISODES.column:     json.dumps(watched_ranges),
            AnimeField.LAST_WATCHED_EPISODE.column: self.last_watched_episode,
            AnimeField.IS_FAVOURITE.column:         int(self.is_favourite),
            AnimeField.IS_WATCHING.column:          int(self.is_watching),
            AnimeField.IS_FINISHED.column:          int(self.is_finished),
            AnimeField.IS_PENDING.column:           int(self.is_pending),
        }

    # ------------------------------------------------------------------
    # Deserialización desde la BD
    # ------------------------------------------------------------------
    @classmethod
    def from_db_dict(cls, data: Dict[str, Any]) -> "AnimeRecord":
        """Construye un ``AnimeRecord`` desde una fila devuelta por ``query_sql``."""
        raw_genres   = data.get(AnimeField.GENRES.column,           "[]") or "[]"
        raw_episodes = data.get(AnimeField.EPISODES.column,         "[]") or "[]"
        raw_watched  = data.get(AnimeField.WATCHED_EPISODES.column, "[]") or "[]"

        try:
            genres: List[str] = json.loads(raw_genres)
        except (json.JSONDecodeError, TypeError):
            genres = []

        try:
            episodes: List[int] = json.loads(raw_episodes)
        except (json.JSONDecodeError, TypeError):
            episodes = []

        try:
            watched_ranges: List[List[int]] = json.loads(raw_watched)
            watched_episodes: Set[int]      = cls._ranges_to_episodes(watched_ranges)
        except (json.JSONDecodeError, TypeError):
            watched_episodes = set()

        return cls(
            id                   = data.get(AnimeField.ID.column),
            anime_id             = str(data.get(AnimeField.ANIME_ID.column, "")),
            title                = data.get(AnimeField.TITLE.column, ""),
            poster_url           = data.get(AnimeField.POSTER_URL.column, ""),
            synopsis             = data.get(AnimeField.SYNOPSIS.column),
            genres               = genres,
            episodes             = episodes,
            watched_episodes     = watched_episodes,
            last_watched_episode = data.get(AnimeField.LAST_WATCHED_EPISODE.column, 0) or 0,
            is_favourite         = bool(data.get(AnimeField.IS_FAVOURITE.column, False)),
            is_watching          = bool(data.get(AnimeField.IS_WATCHING.column,  False)),
            is_finished          = bool(data.get(AnimeField.IS_FINISHED.column,  False)),
            is_pending           = bool(data.get(AnimeField.IS_PENDING.column,   False)),
        )

    # ------------------------------------------------------------------
    # Constructor de conveniencia desde AnimeInfo (API)
    # ------------------------------------------------------------------
    @classmethod
    def from_anime_info(
        cls,
        anime_info:   AnimeInfo,
        is_favourite: bool = False,
        is_watching:  bool = False,
        is_finished:  bool = False,
        is_pending:   bool = False,
    ) -> "AnimeRecord":
        """Crea un ``AnimeRecord`` a partir de un ``AnimeInfo`` de la API."""
        return cls(
            anime_id     = anime_info.id,
            title        = anime_info.title,
            poster_url   = anime_info.poster,
            synopsis     = anime_info.synopsis,
            genres       = anime_info.genres or [],
            episodes     = [ep.id for ep in (anime_info.episodes or [])],
            is_favourite = is_favourite,
            is_watching  = is_watching,
            is_finished  = is_finished,
            is_pending   = is_pending,
        )

    # ------------------------------------------------------------------
    # Helpers de compresión de rangos (uso interno)
    # ------------------------------------------------------------------
    @staticmethod
    def _episodes_to_ranges(episode_ids: Set[int]) -> List[List[int]]:
        """Comprime un conjunto de IDs en rangos: {1,2,3,5} → [[1,3],[5,5]]."""
        if not episode_ids:
            return []
        sorted_ids = sorted(episode_ids)
        ranges: List[List[int]] = []
        start = prev = sorted_ids[0]
        for ep_id in sorted_ids[1:]:
            if ep_id == prev + 1:
                prev = ep_id
            else:
                ranges.append([start, prev])
                start = prev = ep_id
        ranges.append([start, prev])
        return ranges

    @staticmethod
    def _ranges_to_episodes(ranges: List[List[int]]) -> Set[int]:
        """Expande rangos [[1,3],[5,5]] a un conjunto de IDs: {1,2,3,5}."""
        episode_ids: Set[int] = set()
        for r in ranges:
            if len(r) == 2:
                episode_ids.update(range(r[0], r[1] + 1))
        return episode_ids


# ---------------------------------------------------------------------------
# Capa de persistencia
# ---------------------------------------------------------------------------
class AnimesPersistence(ServiceDB):
    DB_NAME     = "DB_Animes.db"
    TABLE_NAME  = "ANIMES"
    FIELDS      = [f.column   for f in AnimeField]
    FIELD_TYPES = [f.sql_type for f in AnimeField]
    PRIMARY_KEY = f"{AnimeField.ID.column} AUTOINCREMENT"

    def __init__(self):
        try:
            self.path_db = get_resource_path(f"resources/DB/{self.DB_NAME}")
            super().__init__(self.path_db)
        except Exception as e:
            print(f"Error al iniciar la base de datos {self.DB_NAME}: {e}")

    def start(self) -> None:
        try:
            if not os.path.isfile(self.path_db):
                if not self._create_db_animes():
                    raise Exception(f"Error al crear la base de datos {self.DB_NAME}")
        except Exception as e:
            print(f"Error al empezar la base de datos {self.DB_NAME}: {e}")

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def get_anime_by_anime_id(self, anime_id: str) -> Optional[AnimeRecord]:
        """Devuelve el ``AnimeRecord`` del anime o ``None`` si no existe en BD."""
        sql = (
            f"SELECT * FROM {self.TABLE_NAME} "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        res, rows = self._db.query_sql(sql, (str(anime_id),), self.FIELDS)
        if not res or not rows:
            return None
        return AnimeRecord.from_db_dict(rows[0])

    def get_watched_episodes(self, anime_id: str) -> Set[int]:
        """Devuelve el conjunto de IDs de episodios vistos para un anime."""
        record = self.get_anime_by_anime_id(anime_id)
        if record is None:
            return set()
        return record.watched_episodes

    def get_favourite_animes(self) -> List[AnimeRecord]:
        """Devuelve todos los animes marcados como favoritos."""
        return self._query_by_status(AnimeStatus.FAVOURITE)

    def get_watching_animes(self) -> List[AnimeRecord]:
        """Devuelve todos los animes en estado «viendo»."""
        return self._query_by_status(AnimeStatus.WATCHING)

    def get_pending_animes(self) -> List[AnimeRecord]:
        """Devuelve todos los animes en estado «pendiente»."""
        return self._query_by_status(AnimeStatus.PENDING)

    def get_finished_animes(self) -> List[AnimeRecord]:
        """Devuelve todos los animes en estado «finalizado»."""
        return self._query_by_status(AnimeStatus.FINISHED)

    def get_anime_by_genre_and_order(
        self,
        status: AnimeStatus,
        genres: List[AnimeGenreFilter],
        order:  AnimeOrderFilter,
    ) -> List[AnimeRecord]:
        """Devuelve animes filtrados por estado, géneros y criterio de orden.

        Si se indican géneros y el orden es ``POR_DEFECTO``, los resultados
        con más coincidencias de género aparecen primero.
        """
        if genres:
            genre_conditions = " OR ".join(
                f"{AnimeField.GENRES.column} LIKE '%\"{g.value}\"%'" for g in genres
            )
            sql = (
                f"SELECT * FROM {self.TABLE_NAME} "
                f"WHERE (({genre_conditions}) AND {status.value} = 1)"
            )
        else:
            sql = f"SELECT * FROM {self.TABLE_NAME} WHERE {status.value} = 1"

        res, rows = self._db.query_sql(sql, tuple(), self.FIELDS)
        if not res or not rows:
            return []

        records = [AnimeRecord.from_db_dict(r) for r in rows]

        if order != AnimeOrderFilter.POR_DEFECTO or not genres:
            return records

        filter_genre_values = {g.value for g in genres}
        records.sort(
            key=lambda r: len(filter_genre_values.intersection(set(r.genres))),
            reverse=True,
        )
        return records

    # ------------------------------------------------------------------
    # Actualizaciones de episodios
    # ------------------------------------------------------------------
    def update_watched_episodes(self, anime_id: str, watched_episode_ids: Set[int]) -> bool:
        """Persiste el conjunto completo de episodios vistos para un anime.

        Si el anime no existe en BD devuelve ``False`` sin hacer nada;
        los episodios vistos solo tienen sentido para animes ya registrados
        en alguna categoría.
        """
        if self.get_anime_by_anime_id(anime_id) is None:
            return False

        ranges       = AnimeRecord._episodes_to_ranges(watched_episode_ids)
        serialized   = json.dumps(ranges)
        last_watched = max(watched_episode_ids) if watched_episode_ids else 0

        sql = (
            f"UPDATE {self.TABLE_NAME} "
            f"SET {AnimeField.WATCHED_EPISODES.column}     = ?, "
            f"    {AnimeField.LAST_WATCHED_EPISODE.column} = ? "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        return self._db.update_sql(sql, (serialized, last_watched, str(anime_id)))

    def update_anime_episodes(self, anime_id: str, episodes: List[EpisodeInfo]) -> bool:
        """Actualiza la lista de episodios de un anime (almacenados en orden descendente)."""
        new_episodes = json.dumps([ep.id for ep in episodes][::-1])
        sql = (
            f"UPDATE {self.TABLE_NAME} "
            f"SET {AnimeField.EPISODES.column} = ? "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        return self._db.update_sql(sql, (new_episodes, str(anime_id)))

    # ------------------------------------------------------------------
    # Actualizaciones de estado: FAVOURITE
    # ------------------------------------------------------------------
    def update_anime_to_favourite(self, anime_info: AnimeInfo) -> bool:
        """Marca un anime como favorito, insertándolo en BD si aún no existe."""
        return self._set_status(anime_info, AnimeStatus.FAVOURITE, value=True)

    def update_anime_to_not_favourite(self, anime_id: str) -> bool:
        """Desmarca un anime como favorito."""
        return self._update_flag(anime_id, AnimeStatus.FAVOURITE, value=False)

    # ------------------------------------------------------------------
    # Actualizaciones de estado: WATCHING
    # ------------------------------------------------------------------
    def update_anime_to_watching(self, anime_info: AnimeInfo) -> bool:
        """Marca un anime como «viendo» (desactiva finished y pending)."""
        return self._set_status(anime_info, AnimeStatus.WATCHING, value=True)

    def update_anime_to_not_watching(self, anime_id: str) -> bool:
        """Desmarca un anime como «viendo» (restaura is_pending si lo tenía antes)."""
        record = self.get_anime_by_anime_id(anime_id)
        if record is None:
            return False
        sql = (
            f"UPDATE {self.TABLE_NAME} "
            f"SET {AnimeField.IS_WATCHING.column} = 0, "
            f"    {AnimeField.IS_PENDING.column}  = ? "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        return self._db.update_sql(sql, (int(record.is_pending), str(anime_id)))

    # ------------------------------------------------------------------
    # Actualizaciones de estado: FINISHED
    # ------------------------------------------------------------------
    def update_anime_to_finished(self, anime_info: AnimeInfo) -> bool:
        """Marca un anime como finalizado (desactiva watching y pending)."""
        return self._set_status(anime_info, AnimeStatus.FINISHED, value=True)

    def update_anime_to_not_finished(self, anime_id: str) -> bool:
        """Desmarca un anime como finalizado (lo mueve a pending y restaura watching)."""
        record = self.get_anime_by_anime_id(anime_id)
        if record is None:
            return False
        sql = (
            f"UPDATE {self.TABLE_NAME} "
            f"SET {AnimeField.IS_FINISHED.column} = 0, "
            f"    {AnimeField.IS_PENDING.column}  = 1, "
            f"    {AnimeField.IS_WATCHING.column} = ? "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        return self._db.update_sql(sql, (int(record.is_watching), str(anime_id)))

    # ------------------------------------------------------------------
    # Actualizaciones de estado: PENDING
    # ------------------------------------------------------------------
    def update_anime_to_pending(self, anime_info: AnimeInfo) -> bool:
        """Marca un anime como pendiente (desactiva finished y watching)."""
        return self._set_status(anime_info, AnimeStatus.PENDING, value=True)

    def update_anime_to_not_pending(self, anime_id: str) -> bool:
        """Desmarca un anime como pendiente."""
        return self._update_flag(anime_id, AnimeStatus.PENDING, value=False)

    # ------------------------------------------------------------------
    # Métodos privados de apoyo
    # ------------------------------------------------------------------
    def _query_by_status(self, status: AnimeStatus) -> List[AnimeRecord]:
        sql = f"SELECT * FROM {self.TABLE_NAME} WHERE {status.value} = 1"
        res, rows = self._db.query_sql(sql, tuple(), self.FIELDS)
        if not res or not rows:
            return []
        return [AnimeRecord.from_db_dict(r) for r in rows]

    def _insert_anime(self, record: AnimeRecord) -> bool:
        """Inserta un ``AnimeRecord`` nuevo en la BD."""
        return self.insert_record_db(self.TABLE_NAME, self.FIELDS, record.to_db_dict())

    def _update_flag(self, anime_id: str, status: AnimeStatus, value: bool) -> bool:
        """Actualiza un único flag de estado para un anime ya existente."""
        sql = (
            f"UPDATE {self.TABLE_NAME} "
            f"SET {status.value} = ? "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        return self._db.update_sql(sql, (int(value), str(anime_id)))

    def _set_status(
        self,
        anime_info: AnimeInfo,
        status:     AnimeStatus,
        value:      bool,
    ) -> bool:
        """Activa o desactiva un estado para un anime.

        Si el anime no existe en BD lo inserta con el estado indicado.
        Si ya existe, actualiza los flags respetando las exclusiones mutuas
        (watching / finished / pending se desactivan entre sí al activarse).
        """
        record = self.get_anime_by_anime_id(str(anime_info.id))

        if record is None:
            new_record = AnimeRecord.from_anime_info(
                anime_info,
                is_favourite = (status == AnimeStatus.FAVOURITE and value),
                is_watching  = (status == AnimeStatus.WATCHING  and value),
                is_finished  = (status == AnimeStatus.FINISHED  and value),
                is_pending   = (status == AnimeStatus.PENDING   and value),
            )
            return self._insert_anime(new_record)

        if status == AnimeStatus.FAVOURITE:
            sql = (
                f"UPDATE {self.TABLE_NAME} "
                f"SET {AnimeField.IS_FAVOURITE.column} = ? "
                f"WHERE {AnimeField.ANIME_ID.column} = ?"
            )
            return self._db.update_sql(sql, (int(value), str(anime_info.id)))

        if status == AnimeStatus.WATCHING:
            sql = (
                f"UPDATE {self.TABLE_NAME} "
                f"SET {AnimeField.IS_WATCHING.column} = ?, "
                f"    {AnimeField.IS_FINISHED.column} = 0, "
                f"    {AnimeField.IS_PENDING.column}  = 0 "
                f"WHERE {AnimeField.ANIME_ID.column} = ?"
            )
            return self._db.update_sql(sql, (int(value), str(anime_info.id)))

        if status == AnimeStatus.FINISHED:
            sql = (
                f"UPDATE {self.TABLE_NAME} "
                f"SET {AnimeField.IS_FINISHED.column} = ?, "
                f"    {AnimeField.IS_WATCHING.column} = 0, "
                f"    {AnimeField.IS_PENDING.column}  = 0 "
                f"WHERE {AnimeField.ANIME_ID.column} = ?"
            )
            return self._db.update_sql(sql, (int(value), str(anime_info.id)))

        if status == AnimeStatus.PENDING:
            sql = (
                f"UPDATE {self.TABLE_NAME} "
                f"SET {AnimeField.IS_PENDING.column}  = ?, "
                f"    {AnimeField.IS_FINISHED.column} = 0, "
                f"    {AnimeField.IS_WATCHING.column} = 0 "
                f"WHERE {AnimeField.ANIME_ID.column} = ?"
            )
            return self._db.update_sql(sql, (int(value), str(anime_info.id)))

        return False

    def _create_db_animes(self) -> bool:
        print(f"Creando base de datos {self.DB_NAME}")
        return self.create_table(self.TABLE_NAME, self.FIELDS, self.FIELD_TYPES, self.PRIMARY_KEY)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class AnimesPersistenceSingleton:
    __instance: Optional[AnimesPersistence] = None

    def __new__(cls) -> AnimesPersistence:
        if cls.__instance is None:
            cls.__instance = AnimesPersistence()
        return cls.__instance