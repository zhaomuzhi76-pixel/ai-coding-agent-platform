from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from backend.workspace.workspace_ignore import (
    WorkspaceIgnorePolicy,
)


class WorkspaceScanner:
    """
    Workspace filesystem scanning boundary.

    Owns:
        - recursive workspace file discovery
        - ignore-policy enforcement
        - metadata extraction

    Does not own:
        - index storage
        - file reading
        - repository operations
        - workspace lifecycle
        - analysis
    """

    VERSION = "2.0"
    MAX_FILES = 50000  # 工业级硬上限：极端大项目兜底
    RESPONSIBILITY = (
        "workspace_filesystem_scanning",
    )

    def __init__(
        self,
        root_path: str,
        ignore_policy: WorkspaceIgnorePolicy | None = None,
    ) -> None:
        if not isinstance(
            root_path,
            str,
        ) or not root_path.strip():
            raise ValueError(
                "workspace root path required"
            )

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

        self.ignore_policy = (
            ignore_policy
            or WorkspaceIgnorePolicy()
        )

    def scan(
        self,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for current, dirs, files in os.walk(
            self.root
        ):
            if len(items) >= self.MAX_FILES:
                break
            current_path = Path(current)

            dirs[:] = [
                name
                for name in dirs
                if not self.ignore_policy.should_ignore(
                    current_path / name
                )
            ]

            for name in files:
                path = (
                    current_path / name
                )

                if self.ignore_policy.should_ignore(
                    path
                ):
                    continue

                items.append(
                    self._metadata(path)
                )

        items.sort(
            key=lambda item: item["path"]
        )

        return items

    def _metadata(
        self,
        path: Path,
    ) -> dict[str, Any]:
        relative = path.relative_to(
            self.root
        )

        # 用 lstat：不跟随符号链接（broken symlink 会抛 OSError）
        try:
            _size = path.lstat().st_size
        except OSError:
            _size = 0

        return {
            "path": relative.as_posix(),
            "name": path.name,
            "suffix": path.suffix.lower(),
            "module": self._module_name(
                relative
            ),
            "size": _size,
        }

    @staticmethod
    def _module_name(
        path: Path,
    ) -> str:
        parts = list(
            path.with_suffix("").parts
        )

        if not parts:
            return ""

        return ".".join(parts)

    def ready(
        self,
    ) -> bool:
        return (
            self.root.exists()
            and self.root.is_dir()
            and self.ignore_policy is not None
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "root": str(self.root),
            "ready": self.ready(),
        }


__all__ = [
    "WorkspaceScanner",
]
