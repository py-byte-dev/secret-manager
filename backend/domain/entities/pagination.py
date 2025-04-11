from collections.abc import Collection
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')


@dataclass(slots=True)
class Pagination(Generic[T]):
    total: int
    size: int
    items: Collection[T]
