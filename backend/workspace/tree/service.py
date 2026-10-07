"""FileTreeService: 工业级文件树服务（L3 装配层）。

组合：
    L0 filter（builtin + gitignore）
    L1 index（mtime 缓存 + invalidator）
    L2 pagination（游标分页 + 流式）

契约：
    - list_dir(path, spec) → CursorPage
    - 保持向后兼容：默认 limit，无分页参数时返回完整
    - 缓存命中：mtime 未变 → 直接返回
    - 忽略规则：builtin + .gitignore（按 root 加载一次）
    - 线程内安全（asyncio 单线程天然安全）

不负责：
    - 磁盘底层读（file_access 管）
    - HTTP / WS 传输（api 层管）
    - 会话 / 项目注册
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .filter.builtin_ignores import BuiltinIgnores
from .filter.gitignore_parser import GitignoreParser
from .index.cache import TreeIndex
from .index.invalidator import MtimeInvalidator
from .pagination.cursor import (
    CursorPage, CursorPaginator, PaginationSpec, DEFAULT_LIMIT,
)


class FileTreeService:
    VERSION = "1.0"

    def __init__(
        self,
        file_access: Any,
        *,
        ignores: BuiltinIgnores | None = None,
        gitignore: GitignoreParser | None = None,
        index: TreeIndex | None = None,
        paginator: CursorPaginator | None = None,
        invalidator: MtimeInvalidator | None = None,
    ) -> None:
        if file_access is None:
            raise ValueError("file_access required")
        if not hasattr(file_access, "root"):
            raise TypeError("file_access must expose .root")

        self.file_access = file_access
        self.root: Path = Path(file_access.root)
        self.ignores = ignores or BuiltinIgnores()
        self.gitignore = gitignore or self._load_gitignore()
        self.index = index or TreeIndex()
        self.paginator = paginator or CursorPaginator()
        self.invalidator = invalidator or MtimeInvalidator()

    # ── 公开 API ──
    def list_dir(
        self,
        path: str = "",
        spec: PaginationSpec | None = None,
        *,
        include_ignored: bool = False,
    ) -> CursorPage:
        """列出目录：缓存 → 过滤 → 分页。"""
        spec = spec or PaginationSpec(limit=DEFAULT_LIMIT)

        # 1. stat 当前目录
        decision = self.invalidator.should_refresh(self.root, path)
        if decision.current_key is None:
            # 目录不存在
            raise FileNotFoundError(
                str(self.root / path) if path else str(self.root)
            )

        # 2. 缓存查询
        cached = self.index.get(
            path,
            decision.current_key.mtime_ns,
            decision.current_key.size,
        )
        if cached is None:
            # 3. 冷路径：从磁盘扫 + 过滤
            raw = self._scan(path)
            filtered = (
                raw if include_ignored
                else self._apply_filters(raw)
            )
            self.index.put(
                path,
                decision.current_key.mtime_ns,
                decision.current_key.size,
                filtered,
            )
            entries = filtered
        else:
            entries = list(cached)

        # 4. 分页
        return self.paginator.paginate(entries, spec)

    def invalidate(self, path: str) -> None:
        self.index.invalidate(path)

    def stats(self) -> dict:
        return {
            "size": self.index.size(),
            "cache": self.index.dump(),
            "ignores": self.ignores.dump(),
            "gitignore": self.gitignore.dump(),
            "paginator": self.paginator.dump(),
        }

    def ready(self) -> bool:
        return (
            self.ignores.ready()
            and self.gitignore.ready()
            and self.index.ready()
            and self.paginator.ready()
        )

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "root": str(self.root),
            "ready": self.ready(),
            "stats": self.stats(),
        }

    # ── 内部 ──
    def _scan(self, path: str) -> list[dict]:
        fs = self.file_access
        if not hasattr(fs, "list_children"):
            raise TypeError("file_access must expose list_children()")
        return fs.list_children(path)

    def _apply_filters(self, entries: list[dict]) -> list[dict]:
        """过滤语义（工业级）：

          1) gitignore 是"用户显式规则"，覆盖 builtin 默认策略
          2) 若 gitignore 明确 negation（!pattern）命中 → 显式重新包含（无论 builtin）
          3) 若 gitignore 明确 ignore 命中 → 忽略
          4) 否则 builtin 判定兜底
        """
        out: list[dict] = []
        has_gi = self.gitignore.rule_count() > 0
        for e in entries:
            name = str(e.get("name", ""))
            is_dir = e.get("kind") == "dir"
            size = int(e.get("size", 0) or 0)
            rel = str(e.get("path", name))

            # 1) gitignore 显式重新包含
            if has_gi:
                gi_matched, gi_negated = self.gitignore.match_verbose(
                    rel, is_dir=is_dir,
                )
                if gi_matched and gi_negated:
                    out.append(e)
                    continue
                if gi_matched and not gi_negated:
                    continue

            # 2) builtin 兜底
            if self.ignores.decide(name, is_dir=is_dir, size=size):
                continue
            out.append(e)
        return out

    def _load_gitignore(self) -> GitignoreParser:
        g = GitignoreParser()
        gi = self.root / ".gitignore"
        try:
            if gi.is_file():
                g.parse(gi.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
        return g


def build_file_tree_service(file_access: Any) -> FileTreeService:
    """工厂：从 file_access 构造完整服务。"""
    return FileTreeService(file_access)


__all__ = ["FileTreeService", "build_file_tree_service"]
