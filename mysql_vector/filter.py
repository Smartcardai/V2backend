from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .collection import PointResult

from .errors import PayloadKeyDoesNotExistError


class Condition(ABC):

    @abstractmethod
    def __call__(self, payload: dict[str, Any]) -> bool:
        return super().__call__(payload)


class FieldCondition(Condition):

    def __init__(self, key: str, condition=Callable[[Any], bool], no_exist_ok=False):
        self.key = key
        self.condition = condition
        self.no_exist_ok = no_exist_ok

    def __call__(self, payload: dict[str, Any]) -> bool:
        if self.key not in payload:
            if not self.no_exist_ok:
                raise PayloadKeyDoesNotExistError(f'Key {self.key!r} not in {payload}')
            else:
                return False
        return self.condition(payload[self.key])


class Filter:
    def __init__(self, match=list[FieldCondition]):
        self.match = match

    def __call__(self, payload: list[PointResult]) -> list[PointResult]:
        return [p for p in payload if all(m(p.payload) for m in self.match)]
