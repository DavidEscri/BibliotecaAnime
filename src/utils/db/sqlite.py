__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils"
__module__ = "sqlite.py"
__version__ = "1.0"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import sqlite3
from sqlite3 import Connection

from utils.utils import get_resource_path

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