from __future__ import annotations

from enum import Enum


class Distance(Enum):
    """
    All the supported distance function used to compare vectors
    """

    def __str__(self) -> str:
        return str(self.value)

    COSINE = 'Cosine'
    EUCLID = 'Euclid'
    DOT = 'Dot'
    MANHATTAN = 'Manhattan'
