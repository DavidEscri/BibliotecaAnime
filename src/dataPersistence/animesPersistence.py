__author__ = "Jose David Escribano Orts"
__subsystem__ = "DataPersistence"
__module__ = "animesPersistence"
__version__ = "2.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any

from APIs.common.models import AnimeInfo, AnimeGenreFilter, AnimeOrderFilter, AnimeProviderId, EpisodeInfo
from utils.db.sqlite import ServiceDB, TableSchema
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
    PROVIDER_ID          = ("provider_id",          "VARCHAR(50)")
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
    provider_id:          Optional[AnimeProviderId] = None
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
            AnimeField.PROVIDER_ID.column:          self.provider_id.value if self.provider_id else None,
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
            provider_id=cls._provider_id_from_db(data.get(AnimeField.PROVIDER_ID.column)),
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

    @staticmethod
    def _provider_id_from_db(raw_value: Optional[str]) -> Optional[AnimeProviderId]:
        """Convierte el texto de la columna ``provider_id`` al enum.

        Es una de las dos fronteras donde el proveedor deja de ser un
        ``AnimeProviderId`` y pasa a ser texto (la otra es ``DB_user.db``).

        Devuelve ``None`` en los dos casos en los que no se sabe de quién es la
        fila, que se tratan igual: la columna está a ``NULL`` (fila anterior a la
        migración), o guarda un proveedor que ya no existe en el código. Nunca
        lanza: un valor raro en una fila no puede impedir leer la biblioteca.
        """
        if not raw_value:
            return None
        try:
            return AnimeProviderId(raw_value)
        except ValueError:
            print(f"Proveedor desconocido en BD: {raw_value!r}; la fila se tratará "
                  f"como si no tuviera proveedor")
            return None

    # ------------------------------------------------------------------
    # Constructor de conveniencia desde AnimeInfo (API)
    # ------------------------------------------------------------------
    @classmethod
    def from_anime_info(
        cls,
        anime_info:   AnimeInfo,
        provider_id:  Optional[AnimeProviderId] = None,
        is_favourite: bool = False,
        is_watching:  bool = False,
        is_finished:  bool = False,
        is_pending:   bool = False,
    ) -> "AnimeRecord":
        """Crea un ``AnimeRecord`` a partir de un ``AnimeInfo`` de la API.

        :param provider_id: proveedor del que salió ``anime_info.id``. Si no se
            indica, se toma el que traiga el propio ``AnimeInfo``. Que la fila
            recuerde su proveedor es lo que evita reabrirla a ciegas más tarde.
        """
        return cls(
            anime_id     = anime_info.id,
            provider_id  = provider_id if provider_id is not None else anime_info.provider_id,
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

    # Esquema declarado de la BD: **la fuente de verdad**. Toda tabla de
    # DB_Animes.db debe figurar aquí; para añadir una tabla nueva basta con
    # añadir su TableSchema a esta lista — validate_db_integrity() la creará
    # en el siguiente arranque, también en instalaciones con datos previos.
    SCHEMA: List[TableSchema] = [
        TableSchema(
            name        = TABLE_NAME,
            fields      = [(f.column, f.sql_type) for f in AnimeField],
            primary_key = PRIMARY_KEY,
        ),
    ]

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
            if not self.validate_db_integrity():
                print(f"Aviso: la base de datos {self.DB_NAME} no concuerda con el esquema "
                      f"declarado en código; puede haber lecturas incorrectas")
        except Exception as e:
            print(f"Error al empezar la base de datos {self.DB_NAME}: {e}")

    # ------------------------------------------------------------------
    # Integridad de esquema
    # ------------------------------------------------------------------
    def validate_db_integrity(self) -> bool:
        """Verifica que la BD física concuerda con ``SCHEMA`` y la corrige si no.

        Se llama desde ``start()`` justo después de comprobar o crear el fichero
        de la BD. Cubre los tres escenarios de evolución del esquema:

        - **columna nueva** en ``AnimeField`` → se añade con ``ALTER TABLE``
          (los registros existentes la reciben a ``NULL`` o a su default).
        - **cambio de orden o de tipo** de las columnas → se reconstruye la
          tabla copiando los datos por nombre de columna.
        - **tabla nueva** añadida a ``SCHEMA`` → se crea.

        Es idempotente: si no hay diferencias no toca la BD ni crea copias. Antes
        de cualquier modificación se guarda una copia del ``.db`` en
        ``resources/DB/backups/``.

        Esto es lo que evita el fallo silencioso de las instalaciones con datos
        previos: ``query_sql`` empareja fila y ``FIELDS`` **por posición**, así
        que una BD antigua con menos columnas devolvería los valores desplazados
        sin lanzar ningún error.

        :return: ``True`` si al terminar la BD concuerda con el esquema.
        """
        print(f"Validando la integridad de {self.DB_NAME}")
        return self.validate_schema(self.SCHEMA)

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

    def get_all_animes(self) -> List[AnimeRecord]:
        """Devuelve **todas** las filas de la biblioteca, en cualquier estado.

        Incluye las que no están en ninguna categoría (todos los flags a 0), que
        siguen ocupando una fila: para detectar si un anime ya está guardado hay
        que mirarlas también, o se acabaría creando un duplicado de algo que ya
        existe.
        """
        sql = f"SELECT * FROM {self.TABLE_NAME}"
        res, rows = self._db.query_sql(sql, tuple(), self.FIELDS)
        if not res or not rows:
            return []
        return [AnimeRecord.from_db_dict(r) for r in rows]

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

    def update_anime_provider_id(self, anime_id: str, provider_id: Optional[AnimeProviderId]) -> bool:
        """Deja constancia de qué proveedor sirve el ``anime_id`` de una fila.

        Se usa para dos cosas distintas:

        - **rellenar** el proveedor de una fila que lo tiene a ``NULL`` (todas las
          anteriores a esta columna) la primera vez que se abre ese anime y se
          sabe quién lo ha servido;
        - **corregirlo** cuando el anime se re-resuelve en otro proveedor.

        Devuelve ``False`` si el anime no está en BD, para no dar por guardado un
        UPDATE que no ha tocado ninguna fila (``SqlUtils.update_sql`` no mira el
        ``rowcount``).
        """
        if self.get_anime_by_anime_id(anime_id) is None:
            return False
        sql = (
            f"UPDATE {self.TABLE_NAME} "
            f"SET {AnimeField.PROVIDER_ID.column} = ? "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        return self._db.update_sql(sql, (provider_id.value if provider_id else None, str(anime_id)))

    def migrate_anime_identity(self, current_anime_id: str, anime_info: AnimeInfo,
                               provider_id: Optional[AnimeProviderId] = None) -> bool:
        """Reapunta una fila ya guardada al anime de **otro proveedor**.

        Es la única operación que reescribe la identidad de una fila existente
        (``anime_id`` y ``provider_id``), y existe porque un *slug* no es
        universal ni eterno: el mismo anime es "one-piece" en AnimeAV1 y
        "one-piece-tv" en AnimeFLV, y hay slugs guardados que su proveedor
        original ya no sirve. Sin esto, la única salida sería borrar el anime y
        volver a añadirlo, perdiendo los episodios vistos.

        **Lo que se conserva** es justamente lo que el usuario ha construido y no
        se puede recuperar de la red: ``watched_episodes``,
        ``last_watched_episode`` y los cuatro estados. Se sobrescribe el resto
        (título, póster, sinopsis, géneros y episodios), porque a partir de ahora
        la fila *es* la del proveedor nuevo y dejar datos del anterior la
        volvería incoherente consigo misma.

        Se niega a migrar si el ``anime_id`` destino ya lo ocupa otra fila: la
        tabla no tiene UNIQUE sobre esa columna, así que el UPDATE pasaría sin
        error y dejaría **dos filas del mismo anime** —cada una con sus propios
        episodios vistos— que ninguna consulta sabría desempatar.

        :param current_anime_id: ``anime_id`` actual de la fila.
        :param anime_info: ficha del proveedor destino; su ``id`` pasa a ser el
            nuevo ``anime_id``.
        :param provider_id: proveedor destino. Si se omite se usa el que traiga
            ``anime_info``.
        :return: ``True`` si la fila se ha actualizado.
        """
        record = self.get_anime_by_anime_id(current_anime_id)
        if record is None:
            print(f"No se puede migrar {current_anime_id}: no está en la biblioteca")
            return False

        new_anime_id = str(anime_info.id)
        if new_anime_id != str(current_anime_id) and self.get_anime_by_anime_id(new_anime_id) is not None:
            print(f"No se puede migrar {current_anime_id} a {new_anime_id}: "
                  f"ya hay otra fila con ese identificador")
            return False

        new_provider_id = provider_id if provider_id is not None else anime_info.provider_id
        # Los episodios se guardan invertidos, pero `record.episodes` ya viene tal
        # cual está en la BD: si hay que conservarlos, se vuelven a escribir sin
        # invertir. Invertirlos otra vez los dejaría al revés.
        new_episode_ids = [ep.id for ep in (anime_info.episodes or [])]
        episodes_json = json.dumps(new_episode_ids[::-1] if new_episode_ids else record.episodes)

        sql = (
            f"UPDATE {self.TABLE_NAME} "
            f"SET {AnimeField.PROVIDER_ID.column} = ?, "
            f"    {AnimeField.ANIME_ID.column}    = ?, "
            f"    {AnimeField.TITLE.column}       = ?, "
            f"    {AnimeField.POSTER_URL.column}  = ?, "
            f"    {AnimeField.SYNOPSIS.column}    = ?, "
            f"    {AnimeField.GENRES.column}      = ?, "
            f"    {AnimeField.EPISODES.column}    = ? "
            f"WHERE {AnimeField.ANIME_ID.column} = ?"
        )
        params = (
            new_provider_id.value if new_provider_id else None,
            new_anime_id,
            anime_info.title    or record.title,
            anime_info.poster   or record.poster_url,
            anime_info.synopsis or record.synopsis,
            json.dumps(anime_info.genres or record.genres),
            episodes_json,
            str(current_anime_id),
        )
        if not self._db.update_sql(sql, params):
            return False
        print(f"Anime {current_anime_id} migrado a {new_anime_id} "
              f"({new_provider_id.value if new_provider_id else 'sin proveedor'}); "
              f"conserva {len(record.watched_episodes)} episodios vistos")
        return True

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

        # La fila ya existe. Si venía sin proveedor (guardada antes de que la
        # columna existiera) y ahora sabemos de quién es su slug, se anota de
        # paso. La ficha ya hace este mismo autorrelleno al abrirse; repetirlo
        # aquí es lo que hace que el invariante «una fila tocada sabe de dónde
        # viene» no dependa de por qué puerta se haya entrado.
        if record.provider_id is None and anime_info.provider_id is not None:
            self.update_anime_provider_id(str(anime_info.id), anime_info.provider_id)

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
        """Crea la BD desde cero con todas las tablas declaradas en ``SCHEMA``."""
        print(f"Creando base de datos {self.DB_NAME}")
        for table_schema in self.SCHEMA:
            if not self._db.create_db(table_schema.create_sql()):
                print(f"Error al crear la tabla {table_schema.name} en {self.path_db}")
                return False
            print(f"Tabla {table_schema.name} creada en {self.path_db}")
        return True


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
class AnimesPersistenceSingleton:
    __instance: Optional[AnimesPersistence] = None

    def __new__(cls) -> AnimesPersistence:
        if cls.__instance is None:
            cls.__instance = AnimesPersistence()
        return cls.__instance