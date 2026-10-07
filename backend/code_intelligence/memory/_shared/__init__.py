"""Shared memory utilities."""
from backend.code_intelligence.memory._shared.schema import (
    open_db,
    with_cursor,
)
from backend.code_intelligence.memory._shared.singleton import (
    SingletonMixin,
)
from backend.code_intelligence.memory._shared.stats import (
    count_rows,
)

__all__ = ["open_db", "with_cursor", "SingletonMixin", "count_rows"]
