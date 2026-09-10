from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PagedResultDto(Generic[T]):
    """Seitenweises Suchergebnis. `total` ist die Trefferzahl ohne Limit."""

    items: list[T]
    total: int
    limit: int
    offset: int
