__author__ = "Jose David Escribano Orts"
__subsystem__ = "DataPersistence"
__module__ = "userPersistence.py"
__version__ = "0.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from utils.db.sqlite import ServiceDB, TableSchema
from utils.utils import get_resource_path


# ---------------------------------------------------------------------------
# Enums de dominio
# ---------------------------------------------------------------------------
class UserSettingField(Enum):
    """Define las columnas de la tabla USER_SETTINGS junto con su tipo SQLite.

    Cada miembro expone dos propiedades:
      - ``column``   → nombre de la columna en la BD.
      - ``sql_type`` → tipo SQLite usado al crear la tabla.
    """
    SETTING_KEY   = ("setting_key",   "VARCHAR(100)")
    SETTING_VALUE = ("setting_value", "TEXT")
    UPDATED_AT    = ("updated_at",    "VARCHAR(30)")

    @property
    def column(self) -> str:
        return self.value[0]

    @property
    def sql_type(self) -> str:
        return self.value[1]


class UserSettingKey(Enum):
    """Claves de configuración reconocidas.

    Añadir una preferencia nueva es añadir un miembro aquí: **no** hace falta
    tocar el esquema ni migrar la BD, porque la tabla es clave/valor.
    """
    #: PROVIDER_ID del proveedor de anime predeterminado ("animeav1", "animeflv"...).
    DEFAULT_ANIME_PROVIDER = "default_anime_provider"
    #: Barra lateral plegada ("1") o desplegada ("0").
    SIDEBAR_COLLAPSED = "sidebar_collapsed"
    #: Los últimos animes cuyos episodios se han marcado como vistos, separados
    #: por comas y el más reciente primero.
    LAST_WATCHED_ANIME_IDS = "last_watched_anime_ids"
    #: Criterio de orden de la pestaña «Favoritos»: "rating" o "title".
    FAVOURITES_ORDER = "favourites_order"
    # Reservada para cuando se integren los mangas:
    # DEFAULT_MANGA_PROVIDER = "default_manga_provider"


# ---------------------------------------------------------------------------
# Dataclass de registro
# ---------------------------------------------------------------------------
@dataclass
class UserSetting:
    """Representación tipada de una fila de la tabla USER_SETTINGS."""
    setting_key:   str
    setting_value: Optional[str] = None
    updated_at:    Optional[str] = None

    @classmethod
    def from_db_dict(cls, data: Dict[str, str]) -> "UserSetting":
        """Construye un ``UserSetting`` desde una fila devuelta por ``query_sql``."""
        return cls(
            setting_key   = data.get(UserSettingField.SETTING_KEY.column, ""),
            setting_value = data.get(UserSettingField.SETTING_VALUE.column),
            updated_at    = data.get(UserSettingField.UPDATED_AT.column),
        )


# ---------------------------------------------------------------------------
# Capa de persistencia
# ---------------------------------------------------------------------------
class UserPersistence(ServiceDB):
    DB_NAME     = "DB_user.db"
    TABLE_NAME  = "USER_SETTINGS"
    FIELDS      = [f.column   for f in UserSettingField]
    FIELD_TYPES = [f.sql_type for f in UserSettingField]
    PRIMARY_KEY = UserSettingField.SETTING_KEY.column

    #: Cuántos animes recuerda la banda «Retomar donde lo dejaste».
    MAX_LAST_WATCHED = 3

    #: Valores admitidos para FAVOURITES_ORDER. Son los que se **persisten**; el
    #: texto que se lee en el desplegable vive en la vista, porque es de la
    #: interfaz y puede cambiar sin invalidar lo guardado.
    FAVOURITES_ORDER_RATING = "rating"
    FAVOURITES_ORDER_TITLE  = "title"
    FAVOURITES_ORDERS = (FAVOURITES_ORDER_RATING, FAVOURITES_ORDER_TITLE)

    # Esquema declarado de la BD: **la fuente de verdad**. Toda tabla de
    # DB_user.db debe figurar aquí; validate_db_integrity() la creará o la
    # alineará en el siguiente arranque.
    SCHEMA: List[TableSchema] = [
        TableSchema(
            name        = TABLE_NAME,
            fields      = [(f.column, f.sql_type) for f in UserSettingField],
            primary_key = PRIMARY_KEY,
        ),
    ]

    def __init__(self):
        # `available` marca si la BD es usable. Si no lo es, la aplicación debe
        # seguir arrancando con los valores por defecto de código: perder una
        # preferencia no puede impedir usar la biblioteca.
        self.available: bool = False
        self.path_db: Optional[str] = None
        try:
            self.path_db = get_resource_path(f"resources/DB/{self.DB_NAME}")
            super().__init__(self.path_db)
        except Exception as e:
            print(f"Error al iniciar la base de datos {self.DB_NAME}: {e}")

    def start(self) -> bool:
        """Crea o alinea ``DB_user.db`` y deja la instancia lista para usarse.

        Nunca lanza: si algo falla, ``available`` queda a ``False`` y todas las
        lecturas devolverán el valor por defecto que se les pase.
        """
        try:
            # Si __init__ no pudo llegar a ServiceDB.__init__ (ruta inválida, sin
            # permisos para crear resources/DB...), no hay conexión que usar.
            if self.path_db is None or getattr(self, "_db", None) is None:
                print(f"La base de datos {self.DB_NAME} no está accesible; "
                      f"se usarán las preferencias por defecto")
                return False
            if not os.path.isfile(self.path_db):
                if not self._create_db_user():
                    raise Exception(f"Error al crear la base de datos {self.DB_NAME}")
            if not self.validate_db_integrity():
                print(f"Aviso: la base de datos {self.DB_NAME} no concuerda con el esquema "
                      f"declarado en código; se ignoran las preferencias guardadas")
                return False
            self.available = True
        except Exception as e:
            print(f"Error al empezar la base de datos {self.DB_NAME}: {e}")
            self.available = False
        return self.available

    # ------------------------------------------------------------------
    # Integridad de esquema
    # ------------------------------------------------------------------
    def validate_db_integrity(self) -> bool:
        """Verifica que la BD física concuerda con ``SCHEMA`` y la corrige si no.

        Mismo motor genérico que usa ``AnimesPersistence`` (``ServiceDB.validate_schema``),
        con las mismas garantías: es idempotente y hace una copia previa en
        ``resources/DB/backups/`` antes de la primera modificación. El nombre de la
        copia lleva el *stem* del fichero, así que no colisiona con las de
        ``DB_Animes.db``.

        :return: ``True`` si al terminar la BD concuerda con el esquema.
        """
        print(f"Validando la integridad de {self.DB_NAME}")
        return self.validate_schema(self.SCHEMA)

    # ------------------------------------------------------------------
    # Lectura y escritura de preferencias
    # ------------------------------------------------------------------
    def get_setting(self, key: UserSettingKey, default: Optional[str] = None) -> Optional[str]:
        """Devuelve el valor de una preferencia, o ``default`` si no está guardada."""
        if not self.available:
            return default
        sql = (
            f"SELECT * FROM {self.TABLE_NAME} "
            f"WHERE {UserSettingField.SETTING_KEY.column} = ?"
        )
        res, rows = self._db.query_sql(sql, (key.value,), self.FIELDS)
        if not res or not rows:
            return default
        setting = UserSetting.from_db_dict(rows[0])
        return setting.setting_value if setting.setting_value is not None else default

    def set_setting(self, key: UserSettingKey, value: Optional[str]) -> bool:
        """Guarda (o sobrescribe) el valor de una preferencia.

        Usa ``ON CONFLICT DO UPDATE`` sobre la clave primaria, así que sirve
        igual para la primera escritura y para las siguientes.
        """
        if not self.available:
            print(f"No se pudo guardar la preferencia {key.value}: {self.DB_NAME} no está disponible")
            return False
        sql = (
            f"INSERT INTO {self.TABLE_NAME} "
            f"({UserSettingField.SETTING_KEY.column}, "
            f" {UserSettingField.SETTING_VALUE.column}, "
            f" {UserSettingField.UPDATED_AT.column}) "
            f"VALUES (?, ?, ?) "
            f"ON CONFLICT({UserSettingField.SETTING_KEY.column}) DO UPDATE SET "
            f"{UserSettingField.SETTING_VALUE.column} = excluded.{UserSettingField.SETTING_VALUE.column}, "
            f"{UserSettingField.UPDATED_AT.column}    = excluded.{UserSettingField.UPDATED_AT.column}"
        )
        return self._db.insert_sql(sql, (key.value, value, datetime.now().isoformat(timespec="seconds")))

    def get_all_settings(self) -> Dict[str, Optional[str]]:
        """Devuelve todas las preferencias guardadas como ``{clave: valor}``.

        Útil para depurar; incluye también claves que ya no estén en
        ``UserSettingKey`` (p.ej. de una versión anterior de la app).
        """
        if not self.available:
            return {}
        sql = f"SELECT * FROM {self.TABLE_NAME}"
        res, rows = self._db.query_sql(sql, tuple(), self.FIELDS)
        if not res or not rows:
            return {}
        settings = [UserSetting.from_db_dict(row) for row in rows]
        return {setting.setting_key: setting.setting_value for setting in settings}

    # ------------------------------------------------------------------
    # Atajos tipados
    # ------------------------------------------------------------------
    def get_default_provider_id(self) -> Optional[str]:
        """Devuelve el ``PROVIDER_ID`` del proveedor de anime predeterminado, o ``None``."""
        return self.get_setting(UserSettingKey.DEFAULT_ANIME_PROVIDER)

    def set_default_provider_id(self, provider_id: Optional[str]) -> bool:
        """Guarda el ``PROVIDER_ID`` del proveedor de anime predeterminado.

        ``None`` deja la preferencia sin valor (el usuario ha desfijado el
        proveedor), que ``get_default_provider_id()`` devuelve como ``None`` y la
        GUI interpreta como «usar el predeterminado del registro».
        """
        return self.set_setting(UserSettingKey.DEFAULT_ANIME_PROVIDER, provider_id)

    def get_sidebar_collapsed(self) -> bool:
        """Devuelve si la barra lateral quedó plegada la última vez.

        Sin preferencia guardada —o con la BD no disponible— devuelve ``False``:
        desplegada es el estado que enseña qué hace cada icono, así que es el
        que menos sorprende a quien abre la aplicación por primera vez.
        """
        return self.get_setting(UserSettingKey.SIDEBAR_COLLAPSED, "0") == "1"

    def set_sidebar_collapsed(self, collapsed: bool) -> bool:
        """Guarda si la barra lateral queda plegada.

        Se persiste como ``"1"`` / ``"0"`` y no como ``"True"`` / ``"False"``:
        la columna es TEXT y conviene que el valor sobreviva a leerlo desde
        cualquier sitio sin depender del ``repr`` de Python.
        """
        return self.set_setting(UserSettingKey.SIDEBAR_COLLAPSED, "1" if collapsed else "0")

    def get_last_watched_ids(self) -> List[str]:
        """Devuelve los últimos animes vistos, del más reciente al más antiguo.

        Son ``anime_id`` de la tabla ``ANIMES``, es decir, el *slug* del proveedor
        que guardó cada fila. Puede contener animes que ya no estén en la
        biblioteca (el usuario los quitó después de verlos): quien los pinte debe
        tolerar que ``get_anime_by_anime_id()`` devuelva ``None``.
        """
        raw = self.get_setting(UserSettingKey.LAST_WATCHED_ANIME_IDS, "")
        if not raw:
            return []
        # Los slugs no llevan comas, así que la coma vale de separador sin
        # necesidad de JSON. El filtro descarta cadenas vacías por si la
        # preferencia quedó con comas de más.
        return [anime_id for anime_id in (part.strip() for part in raw.split(",")) if anime_id]

    def push_last_watched_id(self, anime_id: str) -> bool:
        """Pone un anime el primero de la lista de «últimos vistos».

        Si ya estaba, **sube** en vez de duplicarse; la lista se recorta a
        ``MAX_LAST_WATCHED``. Se llama al marcar un episodio como visto, así que
        pasa muchas veces con el mismo identificador: si el anime ya era el
        primero no se escribe nada en la BD.
        """
        anime_id = str(anime_id)
        current = self.get_last_watched_ids()
        if current[:1] == [anime_id]:
            return True
        updated = [anime_id] + [saved for saved in current if saved != anime_id]
        return self.set_setting(
            UserSettingKey.LAST_WATCHED_ANIME_IDS,
            ",".join(updated[:self.MAX_LAST_WATCHED])
        )

    def get_favourites_order(self) -> str:
        """Devuelve el criterio de orden de «Favoritos»: ``"rating"`` o ``"title"``.

        Por defecto ``"rating"``. Un valor guardado que no se reconozca se
        trata como si no hubiera preferencia.

        :return: Criterio de orden guardado, o ``FAVOURITES_ORDER_RATING`` por defecto.
        """
        value = self.get_setting(UserSettingKey.FAVOURITES_ORDER, self.FAVOURITES_ORDER_RATING)
        if value not in self.FAVOURITES_ORDERS:
            return self.FAVOURITES_ORDER_RATING
        return value

    def set_favourites_order(self, order: str) -> bool:
        """Guarda el criterio de orden de «Favoritos». Ignora valores desconocidos."""
        if order not in self.FAVOURITES_ORDERS:
            print(f"Criterio de orden de favoritos desconocido: {order!r}")
            return False
        return self.set_setting(UserSettingKey.FAVOURITES_ORDER, order)

    # ------------------------------------------------------------------
    # Métodos privados de apoyo
    # ------------------------------------------------------------------
    def _create_db_user(self) -> bool:
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
class UserPersistenceSingleton:
    __instance: Optional[UserPersistence] = None

    def __new__(cls) -> UserPersistence:
        if cls.__instance is None:
            cls.__instance = UserPersistence()
        return cls.__instance
