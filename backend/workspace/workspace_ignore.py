"""WorkspaceIgnorePolicy: 兼容层（唯一真源 = BuiltinIgnores）。

契约：
    - should_ignore(Path) → bool（旧 API，保持兼容）
    - 内部委托 tree.filter.BuiltinIgnores 决策
    - 本文件不重复定义任何黑名单

不负责：
    - 规则定义（BuiltinIgnores 管）
    - 文件系统扫描 / 索引
"""
from __future__ import annotations

from pathlib import Path

from backend.workspace.tree.filter.builtin_ignores import (
    BuiltinIgnores,
)


class WorkspaceIgnorePolicy:
    """兼容层：委托 BuiltinIgnores。"""

    VERSION = "2.0"

    def __init__(
        self,
        impl: BuiltinIgnores | None = None,
    ) -> None:
        self._impl = impl or BuiltinIgnores()

    # ── 旧 API（保持签名兼容）──
    def should_ignore(
        self,
        path: Path,
    ) -> bool:
        if not isinstance(path, Path):
            raise TypeError("path must be Path")
        name = path.name
        if not name:
            return True
        # 名字命中任一黑名单即忽略（兼容路径不存在的场景）
        # 真实 scanner 传的 dirs/files 都是真实存在的路径，
        # 此处取"任一命中"更保守，避免路径不存在的测试误判。
        as_dir = self._impl.decide(name, is_dir=True, size=0).ignored
        if as_dir:
            return True
        return self._impl.decide(name, is_dir=False, size=0).ignored

    def ignore_directory(
        self,
        path: Path,
    ) -> bool:
        if not isinstance(path, Path):
            raise TypeError("path must be Path")
        return self._impl.decide(
            path.name,
            is_dir=True,
            size=0,
        ).ignored

    def ignore_file(
        self,
        path: Path,
    ) -> bool:
        if not isinstance(path, Path):
            raise TypeError("path must be Path")
        return self._impl.decide(
            path.name,
            is_dir=False,
            size=0,
        ).ignored

    def ignore_suffix(
        self,
        path: Path,
    ) -> bool:
        if not isinstance(path, Path):
            raise TypeError("path must be Path")
        name = path.name.lower()
        if not name:
            return False
        return self._impl.decide(
            name,
            is_dir=False,
            size=0,
        ).ignored

    # ── 新 API（可选，暴露真源）──
    def decide(
        self,
        name: str,
        *,
        is_dir: bool,
        size: int = 0,
    ):
        return self._impl.decide(name, is_dir=is_dir, size=size)

    def ready(self) -> bool:
        return self._impl.ready()

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "impl": self._impl.dump(),
            "ready": self.ready(),
        }


__all__ = ["WorkspaceIgnorePolicy"]
