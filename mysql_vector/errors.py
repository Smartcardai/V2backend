from __future__ import annotations


class ClientNotInitializedError(Exception):
    """Raised when info that client connection is accessed without client initialization"""

    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class VectorConfigDoesNotExistError(Exception):
    """Raised when vector config is accessed without initialization"""

    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class VectorDimensionDoesNotMatchError(Exception):
    """Raised when the query vector dimension does not match the collection vector dimension"""

    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg
