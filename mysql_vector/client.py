from __future__ import annotations

import math
from types import TracebackType
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from ._sql_queries import Queries
from .collection import Collection
from .collection import CollectionMeta
from .collection import VectorConfig
from .distance import Distance


class Client:
    def __init__(
        self,
        host: str, username: str,
        password: str, port: int = 3306,
        database: str | None = None,
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.username: str = username
        self.password: str = password
        self.database = database

        # self._conn: MySQLConnection
        # self._curr: MySQLCursor

        self._connect()

        # initialize the db
        self._init_db()

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self, type_: type[BaseException] | None,
        value: BaseException | None, traceback: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def version(self) -> str:
        """
        Get the version of the connected client
        """
        self._curr.execute(Queries.get_version())
        return self._curr.fetchall()[0][0]

    def close(self) -> None:
        self._curr.close()
        self._conn.close()

    def _init_db(self) -> None:
        if not self.database:
            self._exec(Queries.create_db())
            self._exec(Queries.switch_to_db())
        self._exec(Queries.drop_collection_proc())
        self._exec(Queries.create_collection_proc())
        self._exec(Queries.drop_dist_cosine_func())
        self._exec(Queries.define_dist_cosine_func())
        self._exec(Queries.drop_dist_euclid_func())
        self._exec(Queries.define_dist_euclid_func())
        self._exec(Queries.drop_dist_dot_func())
        self._exec(Queries.define_dist_dot_func())

    def _connect(self) -> None:
        self._conn: MySQLConnection = mysql.connector.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
        )

        self._curr: MySQLCursor = self._conn.cursor()

    def _commit(self) -> None:
        self._conn.commit()

    def _exec(self, command: str) -> list[tuple[Any, ...]]:
        self._curr.execute(command)
        return self._curr.fetchall()

    def create_collection(self, name: str, dimension: int, distance: Distance = Distance.COSINE) -> Collection:
        self._curr.callproc(
            Queries.create_collection_proc_name(),
            (name, math.ceil(dimension / 8)),
        )
        self._conn.commit()

        new_collection = Collection()
        new_collection._meta = CollectionMeta(client=self, name=name)
        new_collection._vector_config = VectorConfig(
            size=dimension, distance=distance,
        )
        return new_collection

    def delete_collection(self, name: str) -> None:
        self._curr.execute(Queries.delete_collection(name))
