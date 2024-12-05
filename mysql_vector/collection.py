from __future__ import annotations

import json
import math
from typing import Any
from typing import NamedTuple
from typing import TYPE_CHECKING

import numpy as np

from ._sql_queries import Queries
from .distance import Distance
from .errors import ClientNotInitializedError
from .errors import VectorConfigDoesNotExistError

if TYPE_CHECKING:
    from .client import Client


class CollectionMeta(NamedTuple):
    name: str
    client: Client


class VectorConfig(NamedTuple):
    size: int
    distance: Distance


class Point(NamedTuple):
    vector: list[float]  # for now
    payload: dict[str, Any]


class PointResult(NamedTuple):
    vector_id: int
    vector: list[int]
    payload: dict[str, Any]
    similarity: float


class Collection:
    def __init__(self) -> None:
        self._meta: CollectionMeta | None = None
        self._vector_config: VectorConfig | None = None

    @property
    def name(self) -> str:
        if not self._meta:
            raise ClientNotInitializedError('client is not initialized')
        return self._meta.name

    @property
    def vector_size(self) -> int:
        if not self._vector_config:
            raise VectorConfigDoesNotExistError(
                'vector config is not initialized',
            )
        return self._vector_config.size

    @staticmethod
    def _calc_magnitude(vec: list[float]) -> float:
        return np.linalg.norm(np.array(vec))

    @staticmethod
    def _normalize_vec(vec: list[float], magnitude: float, epsilon: float = 10e-6) -> list[float]:
        magnitude = epsilon if magnitude == 0 else magnitude
        return [i / magnitude for i in vec]

    @staticmethod
    def _vec_to_hex(vec: list[float]) -> str:
        """convert the vector into binary representation"""
        binary = ''.join('1' if v > 0 else '0' for v in vec)
        padded = binary.zfill(math.ceil(len(binary) / 8) * 8)

        # covert to hex
        hex_chars = [
            f'{int(padded[i:i + 4], 2):X}' for i in range(0, len(padded), 4)
        ]
        return ''.join(hex_chars).zfill(math.ceil(len(hex_chars)))

    def upload_points(self, points: list[Point]) -> None:
        if not self._meta:
            raise ClientNotInitializedError('Client is not initialized')

        if not self._vector_config:
            raise VectorConfigDoesNotExistError(
                'vector config is not initialized',
            )

        self._meta.client._curr.executemany(
            Queries.insert_to_collection(self.name),
            [
                (
                    json.dumps(p.vector), json.dumps(
                        self._normalize_vec(
                            p.vector, m := self._calc_magnitude(
                                p.vector,
                            ),
                        ),
                    ), m, self._vec_to_hex(p.vector), json.dumps(p.payload),
                )
                for p in points
            ],
        )
        self._meta.client._commit()

    def query_points(self, query: list[float], limit: int = 10) -> list[PointResult]:
        if not self._meta:
            raise ClientNotInitializedError('Client is not initialized')

        if not self._vector_config:
            raise VectorConfigDoesNotExistError(
                'vector config is not initialized',
            )

        if ql := len(query) != self._vector_config.size:
            raise VectorConfigDoesNotExistError(
                f'query dimension does not match vector dimension ({ql} != {self._vector_config.size})',
            )

        normalized_query = self._normalize_vec(
            query, self._calc_magnitude(query),
        )
        query_binary = self._vec_to_hex(query)

        self._meta.client._curr.execute(
            Queries.get_search_candidates(self.name), (query_binary, limit),
        )
        candidates = [row[0] for row in self._meta.client._curr.fetchall()]
        placeholders = ', '.join(['%s'] * len(candidates))

        self._meta.client._curr.execute(
            Queries.get_search_vectors(
                self.name, placeholders, self._vector_config.distance,
            ), (json.dumps(normalized_query), *candidates, limit),
        )
        return [PointResult(*row) for row in self._meta.client._curr.fetchall()]
