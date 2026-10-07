from __future__ import annotations

from collections import defaultdict
from typing import Any


class WorkspaceIndex:
    """
    Workspace metadata index.

    Responsibility:
        - store workspace metadata
        - maintain lookup indexes
        - query indexed data
        - keep secondary indexes consistent

    Not Responsible:
        - scanning
        - filesystem access
        - analysis
        - lifecycle
    """

    VERSION = "3.2"

    def __init__(
        self,
    ) -> None:
        self.workspace = ""

        self.file_index: dict[
            str,
            dict[str, Any],
        ] = {}

        self.module_index: dict[
            str,
            set[str],
        ] = defaultdict(set)

        self.extension_index: dict[
            str,
            set[str],
        ] = defaultdict(set)

    def reset(
        self,
        workspace: str,
    ) -> None:
        self.workspace = workspace
        self.file_index.clear()
        self.module_index.clear()
        self.extension_index.clear()

    def add(
        self,
        metadata: dict[str, Any],
    ) -> None:
        path = metadata.get(
            "path",
            "",
        )

        if not path:
            return

        old = self.file_index.get(path)

        if old:
            self._remove_indexes(old)

        self.file_index[path] = metadata

        module = metadata.get(
            "module",
            "",
        )
        suffix = metadata.get(
            "suffix",
            "",
        )

        if module:
            self.module_index[module].add(path)

        if suffix:
            self.extension_index[suffix].add(path)

    def _remove_indexes(
        self,
        metadata: dict[str, Any],
    ) -> None:
        path = metadata.get(
            "path",
            "",
        )

        module = metadata.get(
            "module",
            "",
        )
        suffix = metadata.get(
            "suffix",
            "",
        )

        if module:
            paths = self.module_index.get(module)
            if paths is not None:
                paths.discard(path)
                if not paths:
                    del self.module_index[module]

        if suffix:
            paths = self.extension_index.get(suffix)
            if paths is not None:
                paths.discard(path)
                if not paths:
                    del self.extension_index[suffix]

    def files(
        self,
    ) -> list[dict[str, Any]]:
        return list(
            self.file_index.values()
        )

    def modules(
        self,
    ) -> dict[str, list[str]]:
        return {
            module: sorted(paths)
            for module, paths in self.module_index.items()
            if paths
        }

    def extensions(
        self,
    ) -> dict[str, list[str]]:
        return {
            suffix: sorted(paths)
            for suffix, paths in self.extension_index.items()
            if paths
        }

    def find_file(
        self,
        keyword: str,
    ) -> list[dict[str, Any]]:
        keyword = keyword.lower()

        return [
            item
            for item in self.file_index.values()
            if keyword in item.get(
                "path",
                "",
            ).lower()
        ]

    def find_module(
        self,
        keyword: str,
    ) -> dict[str, list[str]]:
        keyword = keyword.lower()

        return {
            module: sorted(files)
            for module, files in self.module_index.items()
            if keyword in module.lower()
            and files
        }

    def ready(
        self,
    ) -> bool:
        return bool(
            self.workspace
        )

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name": "WorkspaceIndex",
            "version": self.VERSION,
            "workspace": self.workspace,
            "files": len(
                self.file_index
            ),
            "modules": len(
                self.module_index
            ),
            "extensions": len(
                self.extension_index
            ),
        }


__all__ = [
    "WorkspaceIndex",
]
