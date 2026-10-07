"""CursorPaginator: 稳定游标分页。

契约：
  - 排序固定：dir 优先 + name 字典序（与 list_children 一致）
  - 游标 = 上一页最后一条的 name（稳定，不受插入/删除干扰）
  - limit 硬上限（默认 500，上限 5000）
  - 返回 {entries, total, more, next_cursor}

不负责：
  - 磁盘扫描（调用方传 entries）
  - 忽略过滤 / 缓存
  - 流式（streamer 管）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


DEFAULT_LIMIT = 200
HARD_LIMIT = 5000


@dataclass(frozen=True, slots=True)
class PaginationSpec:
    limit: int = DEFAULT_LIMIT
    cursor: str = ""     # 上一页最后一条的 name

    def __post_init__(self) -> None:
        if not isinstance(self.limit, int) or self.limit < 1:
            raise ValueError("limit must be int >= 1")
        if self.limit > HARD_LIMIT:
            raise ValueError(f"limit exceeds hard cap {HARD_LIMIT}")
        if not isinstance(self.cursor, str):
            raise TypeError("cursor must be str")


@dataclass(frozen=True, slots=True)
class CursorPage:
    entries: tuple
    total: int
    more: bool
    next_cursor: str

    def to_dict(self) -> dict:
        return {
            "entries": list(self.entries),
            "total": self.total,
            "more": self.more,
            "next_cursor": self.next_cursor,
        }


def _sort_key(e: dict) -> tuple:
    kind = e.get("kind", "file")
    name = e.get("name", "")
    return (0 if kind == "dir" else 1, name)


class CursorPaginator:
    VERSION = "1.0"

    def __init__(self, hard_limit: int = HARD_LIMIT) -> None:
        if hard_limit < 1:
            raise ValueError("hard_limit must be >= 1")
        self.hard_limit = int(hard_limit)

    def paginate(
        self,
        entries: Iterable[dict],
        spec: PaginationSpec,
    ) -> CursorPage:
        if not isinstance(spec, PaginationSpec):
            raise TypeError("spec must be PaginationSpec")
        arr = sorted((dict(e) for e in entries), key=_sort_key)
        total = len(arr)

        # 定位游标起点（严格 > cursor 之后）
        start = 0
        if spec.cursor:
            found = False
            for i, e in enumerate(arr):
                if e.get("name", "") == spec.cursor:
                    start = i + 1
                    found = True
                    break
            if not found:
                # 游标失效（可能被删）→ 从头开始
                start = 0

        limit = min(spec.limit, self.hard_limit)
        page = arr[start:start + limit]
        more = (start + len(page)) < total
        next_cursor = page[-1].get("name", "") if page and more else ""

        return CursorPage(
            entries=tuple(page),
            total=total,
            more=more,
            next_cursor=next_cursor,
        )

    def ready(self) -> bool:
        return self.hard_limit >= 1

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "hard_limit": self.hard_limit,
            "ready": self.ready(),
        }


__all__ = [
    "CursorPaginator", "CursorPage", "PaginationSpec",
    "DEFAULT_LIMIT", "HARD_LIMIT",
]
