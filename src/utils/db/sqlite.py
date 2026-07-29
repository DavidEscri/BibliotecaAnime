__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils.db"
__module__ = "sqlite.py"
__version__ = "1.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from sqlite3 import Connection
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Afinidades de tipo de SQLite
# ---------------------------------------------------------------------------
def sqlite_affinity(declared_type: str) -> str:
    """Devuelve la afinidad SQLite de un tipo declarado.

    Implementa las 5 reglas de determinación de afinidad de SQLite
    (https://sqlite.org/datatype3.html#determination_of_column_affinity).
    Se usa para comparar esquemas: ``VARCHAR(100)`` y ``VARCHAR(200)`` tienen
    la misma afinidad (TEXT) y por tanto son equivalentes, mientras que
    ``INTEGER`` y ``VARCHAR(100)`` no lo son.
    """
    upper = (declared_type or "").upper()
    if "INT" in upper:
        return "INTEGER"
    if "CHAR" in upper or "CLOB" in upper or "TEXT" in upper:
        return "TEXT"
    if "BLOB" in upper or not upper:
        return "BLOB"
    if "REAL" in upper or "FLOA" in upper or "DOUB" in upper:
        return "REAL"
    return "NUMERIC"


# ---------------------------------------------------------------------------
# Declaración de esquema
# ---------------------------------------------------------------------------
@dataclass
class TableSchema:
    """Esquema declarativo de una tabla: la fuente de verdad en código.

    ``fields`` es una lista ordenada de ``(columna, tipo_sqlite)``. El orden
    importa: ``SqlUtils.query_sql`` empareja fila y campos **por posición**.

    ``defaults`` permite fijar el valor por defecto (expresión SQL literal) de
    columnas concretas; se aplica tanto al crear la tabla como al añadir una
    columna nueva a una tabla ya existente.
    """
    name:        str
    fields:      List[Tuple[str, str]]
    primary_key: Optional[str]   = None
    defaults:    Dict[str, Any]  = field(default_factory=dict)

    @property
    def columns(self) -> List[str]:
        return [column for column, _ in self.fields]

    @property
    def types(self) -> List[str]:
        return [sql_type for _, sql_type in self.fields]

    def column_definition(self, column: str, sql_type: str) -> str:
        """Devuelve la definición SQL de una columna, con su default si lo tiene."""
        definition = f"{column} {sql_type}"
        if column in self.defaults:
            definition += f" DEFAULT {self.defaults[column]}"
        return definition

    def create_sql(self, table_name: Optional[str] = None) -> str:
        """Genera el ``CREATE TABLE`` de este esquema.

        ``table_name`` permite crear la tabla con otro nombre (usado por la
        reconstrucción, que trabaja sobre una tabla temporal).
        """
        definitions = [self.column_definition(c, t) for c, t in self.fields]
        if self.primary_key:
            definitions.append(f"PRIMARY KEY ({self.primary_key})")
        return f"CREATE TABLE IF NOT EXISTS {table_name or self.name} ({', '.join(definitions)})"


class SqlUtils:

    def __init__(self, path: str):
        self._path = path

    def insert_sql(self, sql: str, params: tuple) -> bool:
        connection: Connection = None
        check: bool = False
        try:
            connection = sqlite3.connect(self._path)
            cursor = connection.cursor()
            cursor.execute(sql, params)
            connection.commit()
            check = True
        except Exception as ex:
            print(f"Error al insertar en la base de datos: {ex}")
        finally:
            if connection:
                connection.close()
        return check

    def update_sql(self, sql: str, params: tuple) -> bool:
        connection: Connection = None
        check: bool = False
        try:
            connection = sqlite3.connect(self._path)
            cursor = connection.cursor()
            cursor.execute(sql, params)
            connection.commit()
            check = True
        except Exception as ex:
            print(f"Error al actualizar en la base de datos: {ex}")
        finally:
            if connection:
                connection.close()
        return check

    def query_sql(self, sql: str, params: tuple, list_field: list) -> (bool, list):
        connection: Connection = None
        check = [False, None]
        list_res: list = []
        try:
            connection = sqlite3.connect(self._path)
            cursor = connection.cursor()
            cursor.execute(sql, params)
            register = cursor.fetchall()
            for i in register:
                counter = 0
                res = dict()
                for j in list_field:
                    res[j] = i[counter]
                    counter += 1
                list_res.append(res)
            check = [True, list_res]
        except Exception as ex:
            print(f"Error al obtener el registro desde la DB: {ex}")
        finally:
            if connection:
                connection.close()
        return check[0], check[1]

    def create_db(self, sql: str) -> bool:
        check = False
        connection: Connection = None
        try:
            connection = sqlite3.connect(self._path)
            cursor = connection.cursor()
            cursor.execute(sql)
            connection.commit()
            check = True
        except Exception as ex:
            print(f"Error al crear DB: {ex}", )
        finally:
            if connection:
                connection.close()
        return check

    def execute_transaction(self, statements: List[str]) -> bool:
        """Ejecuta varias sentencias en una única transacción, todo o nada.

        Si alguna falla se hace ``ROLLBACK`` y la BD queda como estaba. Se usa
        para las migraciones de esquema, donde una reconstrucción a medias
        dejaría la tabla en un estado inservible.
        """
        connection: Connection = None
        check: bool = False
        try:
            connection = sqlite3.connect(self._path)
            # isolation_level=None desactivaría el manejo implícito; aquí
            # dejamos que sqlite3 abra la transacción con el primer DML.
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("BEGIN")
            for sql in statements:
                cursor.execute(sql)
            connection.commit()
            check = True
        except Exception as ex:
            print(f"Error al ejecutar la transacción, se deshacen los cambios: {ex}")
            if connection:
                try:
                    connection.rollback()
                except Exception as rollback_ex:
                    print(f"Error al deshacer la transacción: {rollback_ex}")
        finally:
            if connection:
                connection.close()
        return check

    def get_table_names(self) -> List[str]:
        """Devuelve los nombres de las tablas de usuario de la BD."""
        connection: Connection = None
        tables: List[str] = []
        try:
            connection = sqlite3.connect(self._path)
            cursor = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]
        except Exception as ex:
            print(f"Error al obtener las tablas de la DB: {ex}")
        finally:
            if connection:
                connection.close()
        return tables

    def get_table_columns(self, table_name: str) -> List[Tuple[str, str]]:
        """Devuelve ``[(columna, tipo_declarado), …]`` en el orden físico de la tabla."""
        connection: Connection = None
        columns: List[Tuple[str, str]] = []
        try:
            connection = sqlite3.connect(self._path)
            cursor = connection.execute(f"PRAGMA table_info({table_name})")
            columns = [(row[1], row[2]) for row in cursor.fetchall()]
        except Exception as ex:
            print(f"Error al obtener las columnas de {table_name}: {ex}")
        finally:
            if connection:
                connection.close()
        return columns

    def get_conn(self) -> Connection:
        return sqlite3.connect(self._path)


class ServiceDB:
    def __init__(self, db_path: str):
        dir_path = os.path.dirname(db_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self.path_db = db_path
        self._db = SqlUtils(self.path_db)

    def create_table(self, table_name: str, list_fields: list, list_fields_type: list, primary_key: str) -> bool:
        fields: list = list()
        for i in range(0, len(list_fields)):
            fields.append(f"{list_fields[i]} {list_fields_type[i]}")
        fields.append(f"PRIMARY KEY ({primary_key})")
        sql: str = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(fields)})"
        result: bool = self._db.create_db(sql)
        if result:
            print(f"Tabla {table_name} creada en {self.path_db}")
        else:
            print(f"Error al crear tabla {table_name} creada en {self.path_db}")
        return result

    # ------------------------------------------------------------------
    # Migraciones de esquema
    # ------------------------------------------------------------------
    def validate_schema(self, schemas: List[TableSchema], backup: bool = True) -> bool:
        """Compara el esquema físico de la BD con el declarado y lo corrige.

        Para cada tabla de ``schemas`` decide la acción mínima necesaria:

        - la tabla no existe            → ``CREATE TABLE``
        - solo faltan columnas al final → ``ALTER TABLE ADD COLUMN`` (sin mover datos)
        - cualquier otra diferencia     → reconstrucción de la tabla en una
          transacción, copiando por **nombre de columna** los datos existentes

        Se hace una copia de seguridad del fichero ``.db`` antes de la primera
        modificación (salvo ``backup=False``). Devuelve ``True`` si al terminar
        la BD concuerda con lo declarado.
        """
        if not schemas:
            return True

        pending = [(schema, self.diff_table(schema)) for schema in schemas]
        pending = [(schema, diff) for schema, diff in pending if diff["needs_migration"]]

        if not pending:
            print(f"Esquema de {os.path.basename(self.path_db)} correcto, no hay nada que migrar")
            return True

        if backup and os.path.isfile(self.path_db) and not self.backup_db():
            print("No se pudo crear la copia de seguridad, se aborta la migración")
            return False

        all_ok = True
        for schema, diff in pending:
            if not self.apply_table_migration(schema, diff):
                all_ok = False
                continue
            # Verificación posterior: la tabla debe concordar ya con lo declarado.
            if self.diff_table(schema)["needs_migration"]:
                print(f"La tabla {schema.name} sigue sin concordar con el esquema declarado")
                all_ok = False
        return all_ok

    def diff_table(self, schema: TableSchema) -> Dict[str, Any]:
        """Compara una tabla física con su esquema declarado.

        Devuelve un diccionario con las diferencias encontradas:
        ``exists``, ``missing`` (columnas declaradas que no están),
        ``extra`` (columnas en BD no declaradas), ``retyped`` (columnas cuya
        afinidad no coincide), ``reordered`` (el orden físico no coincide) y
        ``needs_migration``.
        """
        current = self._db.get_table_columns(schema.name)
        if not current:
            return {
                "exists": False, "missing": schema.columns, "extra": [],
                "retyped": [], "reordered": False, "needs_migration": True,
            }

        current_types = {column: sql_type for column, sql_type in current}
        current_order = [column for column, _ in current]
        declared      = dict(schema.fields)

        missing = [c for c in schema.columns  if c not in current_types]
        extra   = [c for c in current_order   if c not in declared]
        retyped = [
            c for c in schema.columns
            if c in current_types
            and sqlite_affinity(current_types[c]) != sqlite_affinity(declared[c])
        ]
        # El orden solo se compara sobre las columnas que ya existen: las que
        # faltan se añadirán al final y se evalúan aparte.
        reordered = [c for c in current_order if c in declared] != \
                    [c for c in schema.columns if c in current_types]

        return {
            "exists": True, "missing": missing, "extra": extra,
            "retyped": retyped, "reordered": reordered,
            "needs_migration": bool(missing or extra or retyped or reordered),
        }

    def apply_table_migration(self, schema: TableSchema, diff: Dict[str, Any]) -> bool:
        """Aplica la corrección mínima que resuelve el ``diff`` de una tabla."""
        if not diff["exists"]:
            print(f"Migración: la tabla {schema.name} no existe, se crea")
            return self._db.create_db(schema.create_sql())

        # Caso barato: solo faltan columnas y las que hay están en orden. Al
        # añadirlas SQLite las coloca al final, que es justo donde el esquema
        # declarado las espera.
        only_appends = (
            diff["missing"] and not diff["extra"]
            and not diff["retyped"] and not diff["reordered"]
            and schema.columns[:-len(diff["missing"])] ==
                [c for c in schema.columns if c not in diff["missing"]]
        )
        if only_appends:
            print(f"Migración: se añaden a {schema.name} las columnas {diff['missing']}")
            declared = dict(schema.fields)
            statements = [
                f"ALTER TABLE {schema.name} "
                f"ADD COLUMN {schema.column_definition(column, declared[column])}"
                for column in diff["missing"]
            ]
            return self._db.execute_transaction(statements)

        return self.__rebuild_table(schema, diff)

    def __rebuild_table(self, schema: TableSchema, diff: Dict[str, Any]) -> bool:
        """Reconstruye una tabla con el esquema declarado, conservando los datos.

        Crea una tabla temporal con el esquema correcto, copia los datos
        emparejando **por nombre de columna** (no por posición), borra la
        original y renombra. Todo en una transacción.

        Las columnas presentes en la BD pero no declaradas en el esquema **se
        pierden en la tabla resultante** (siguen en la copia de seguridad); se
        avisa por consola.
        """
        reasons = []
        if diff["missing"]:   reasons.append(f"faltan columnas {diff['missing']}")
        if diff["retyped"]:   reasons.append(f"tipos distintos en {diff['retyped']}")
        if diff["reordered"]: reasons.append("orden de columnas distinto")
        if diff["extra"]:     reasons.append(f"columnas no declaradas {diff['extra']}")
        print(f"Migración: se reconstruye la tabla {schema.name} ({'; '.join(reasons)})")
        if diff["extra"]:
            print(f"  Aviso: se descartan las columnas {diff['extra']}, "
                  f"conservadas en la copia de seguridad")

        current   = [column for column, _ in self._db.get_table_columns(schema.name)]
        preserved = [column for column in schema.columns if column in current]
        if not preserved:
            print(f"  Error: ninguna columna de {schema.name} es reutilizable, se aborta")
            return False

        temp_name    = f"{schema.name}__migration"
        column_list  = ", ".join(preserved)
        return self._db.execute_transaction([
            f"DROP TABLE IF EXISTS {temp_name}",
            schema.create_sql(temp_name),
            f"INSERT INTO {temp_name} ({column_list}) SELECT {column_list} FROM {schema.name}",
            f"DROP TABLE {schema.name}",
            f"ALTER TABLE {temp_name} RENAME TO {schema.name}",
        ])

    def backup_db(self) -> bool:
        """Copia el fichero ``.db`` a ``backups/<nombre>_<timestamp>.db``."""
        try:
            backups_dir = os.path.join(os.path.dirname(self.path_db), "backups")
            os.makedirs(backups_dir, exist_ok=True)
            stem, extension = os.path.splitext(os.path.basename(self.path_db))
            timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backups_dir, f"{stem}_{timestamp}{extension}")
            # sqlite3.Connection.backup usa la API de backup de SQLite: copia
            # consistente incluso con la BD abierta por otra conexión.
            source = sqlite3.connect(self.path_db)
            target = sqlite3.connect(backup_path)
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()
            print(f"Copia de seguridad creada en {backup_path}")
            return True
        except Exception as ex:
            print(f"Error al crear la copia de seguridad de {self.path_db}: {ex}")
            return False

    @staticmethod
    def validate_record(list_fields: list, record: dict) -> bool:
        if not all(item in list_fields for item in list(record.keys())):
            return False
        else:
            return True

    def insert_record_db(self, table_name: str, list_fields: list, record: dict) -> (bool, int):
        """
        Método abstracto para insertar un registro en la DB
        """
        if not self.validate_record(list_fields, record):
            print(f"Parámetros de entrada en el insert de {table_name} no son correctos")
            return False, 0

        fields: list = list()
        params: list = list()
        lq: list = list()

        for i in range(0, len(list_fields)):
            fields.append(list_fields[i])
            if record[list_fields[i]] == "NULL":
                lq.append("NULL")
            else:
                params.append(record[list_fields[i]])
                lq.append("?")

        sql: str = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({', '.join(lq)})"
        return self._db.insert_sql(sql, tuple(params))