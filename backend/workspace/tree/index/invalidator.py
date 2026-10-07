"""MtimeInvalidator: 判断缓存条目是否失效。

契约：
  - compare(key_a, key_b) → 是否相同（不同=失效）
  - should_refresh(path) → 通过 stat 单次查询决定
  - 是纯策略，不持有缓存

不负责：
  - 缓存存储（cache 层管）
  - 目录扫描
  - 忽略过滤
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .cache import MtimeKey


@dataclass(frozen=True, slots=True)
class InvalidatorDecision:
    should_refresh: bool
    reason: str
    current_key: MtimeKey | None


class MtimeInvalidator:
    VERSION = "1.0"

    def compare(self, old: MtimeKey, new: MtimeKey) -> bool:
        """返回 True = 相同（有效），False = 失效。"""
        if not isinstance(old, MtimeKey) or not isinstance(new, MtimeKey):
            raise TypeError("both must be MtimeKey")
        return old == new

    def should_refresh(self, root: Path, rel_path: str) -> InvalidatorDecision:
        if not isinstance(root, Path):
            raise TypeError("root must be Path")
        target = root / rel_path if rel_path else root
        try:
            st = os.stat(target)
        except FileNotFoundError as exc:
            return InvalidatorDecision(True, "missing:" + str(exc), None)
        except OSError as exc:
            return InvalidatorDecision(True, "os-error:" + str(exc), None)
        if not os.path.isdir(target):
            return InvalidatorDecision(True, "not-a-dir", None)
        return InvalidatorDecision(
            False, "ok",
            MtimeKey(rel_path, st.st_mtime_ns, st.st_size),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION}


__all__ = ["MtimeInvalidator", "InvalidatorDecision"]
