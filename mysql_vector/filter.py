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

    def __and__(self, other: Condition) -> Condition:
        return CombinedCondition(self, other, op="and")

    def __or__(self, other: Condition) -> Condition:
        return CombinedCondition(self, other, op="or")


class CombinedCondition(Condition):
    def __init__(self, cond1: Condition, cond2: Condition, op: str):
        if op not in {"and", "or"}:
            raise ValueError("Invalid operator for combination: must be 'and' or 'or'.")
        self.cond1 = cond1
        self.cond2 = cond2
        self.op = op

    def __call__(self, payload: dict[str, Any]) -> bool:
        if self.op == "and":
            return self.cond1(payload) and self.cond2(payload)
        elif self.op == "or":
            return self.cond1(payload) or self.cond2(payload)


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
