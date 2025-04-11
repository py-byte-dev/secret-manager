from collections.abc import Collection
from typing import TypeVar

from backend.domain.entities.pagination import Pagination

T = TypeVar('T')


class PaginationService:
    @staticmethod
    def create_page(page: int, page_size: int, items: Collection[T]) -> Pagination[T]:
        offset = (page - 1) * page_size

        return Pagination[T](
            total=len(items),
            size=page_size,
            items=items[offset : offset + page_size],
        )
