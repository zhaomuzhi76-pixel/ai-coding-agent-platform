"""Mixin 1 of WorkspaceFileAccess."""
from __future__ import annotations
from .part1 import (Path, WorkspaceIgnorePolicy,)  # noqa: F401
class _Mixin1:
    def __init__(
        self,
        root_path: str,
        *,
        ignore_policy: WorkspaceIgnorePolicy | None = None,
    ) -> None:
        self._ignore = ignore_policy or WorkspaceIgnorePolicy()

        self.root = (
            Path(root_path)
            .expanduser()
            .resolve()
        )

        if not self.root.exists():
            raise FileNotFoundError(
                str(self.root)
            )

        if not self.root.is_dir():
            raise NotADirectoryError(
                str(self.root)
            )

    def resolve(
        self,
        path: str,
    ) -> Path:

        # strict=False：允许 broken symlink（不然遇到悬空符号链接会 500）
        target = (
            self.root / path
        ).resolve(strict=False)

        try:
            target.relative_to(
                self.root
            )
        except ValueError:
            raise PermissionError(
                "Path traversal detected"
            )

        return target

    def exists(
        self,
        path: str,
    ) -> bool:

        return self.resolve(
            path
        ).exists()

    def read_text(
        self,
        path: str,
    ) -> str:

        target = self.resolve(
            path
        )

        self._guard_read(target)

        if not target.exists():
            raise FileNotFoundError(
                str(target)
            )

        if not target.is_file():
            raise IsADirectoryError(
                str(target)
            )

        return target.read_text(
            encoding="utf-8"
        )

    def _guard_read(self, target: Path) -> None:
        """读保护：只挡敏感文件（凭据/密钥），不挡 .git 目录内文件。"""
        name = target.name
        if not name:
            return
        decision = self._ignore.decide(name, is_dir=False, size=0)
        if decision.ignored:
            try:
                rel = target.relative_to(self.root)
            except ValueError:
                rel = target
            raise PermissionError(
                f"protected path (read denied): {rel.as_posix()} "
                f"[{decision.reason}]"
            )

    def _guard_write(self, target: Path) -> None:
        """逐段检查路径祖先，命中保护名单 → 拒绝写。"""
        try:
            rel = target.relative_to(self.root)
        except ValueError:
            return  # resolve 已保证在 root 内
        cur = self.root
        for part in rel.parts:
            cur = cur / part
            if self._ignore.should_ignore(cur):
                raise PermissionError(
                    f"protected path (write denied): {rel.as_posix()}"
                )

    def write_text(
        self,
        path: str,
        content: str,
    ) -> None:

        target = self.resolve(
            path
        )

        self._guard_write(target)

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

    def list_children(
        self,
        path: str = "",
    ) -> list[dict]:
        """列出目录直接子项（文件树持久化基础）。

        契约：
          - 从磁盘实时扫（不做缓存）→ 真持久化
          - posix 排序：目录优先，再按名称
          - 返回结构化条目：[{name, path, kind, size, mtime}]
          - 隐藏文件默认包含（.git 等由调用方过滤）
          - 越权访问抛 PermissionError（复用 resolve）

        Not responsible:
          - 递归展开（调用方按需多次调用）
          - 索引 / 缓存 / 文件监控
        """
        target = self.resolve(path)
        if not target.exists():
            raise FileNotFoundError(str(target))
        if not target.is_dir():
            raise NotADirectoryError(str(target))

        entries: list[dict] = []
        try:
            children = list(target.iterdir())
        except OSError:
            children = []
        for child in children:
            try:
                # 用 lstat 语义（不跟进符号链接），避免 broken symlink 抛错
                stat = child.lstat()
                is_dir = child.is_dir() and not child.is_symlink() or (
                    child.is_symlink() and child.exists() and child.is_dir()
                )
                # 若 symlink 悬空 → is_dir=False；若正常 → 按实际
                if not is_dir:
                    is_dir = False
            except OSError:
                continue
            rel = child.relative_to(self.root).as_posix()
            entries.append({
                "name": child.name,
                "path": rel,
                # 前端契约：type = file / directory
                "type": "directory" if is_dir else "file",
                # 树层内部契约：kind = dir / file
                "kind": "dir" if is_dir else "file",
                "size": 0 if is_dir else int(stat.st_size),
                "mtime": int(stat.st_mtime),
            })

        entries.sort(key=lambda e: (0 if e["kind"] == "dir" else 1, e["name"]))
        return entries

    def ready(
        self,
    ) -> bool:

        return self.root.exists()
