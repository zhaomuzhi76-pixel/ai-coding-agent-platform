from __future__ import annotations

from typing import Any

from backend.workspace.workspace_index import WorkspaceIndex


class WorkspaceFileQuery:
    """
    Workspace indexed file query service.

    Responsibility:
        - query workspace index
        - filter indexed files

    Not Responsible:
        - scanning
        - file access
        - indexing build
        - analysis
    """

    VERSION = "2.1"

    def __init__(
        self,
        index: WorkspaceIndex,
    ) -> None:

        if index is None:
            raise ValueError(
                "WorkspaceFileQuery requires index"
            )

        self.index = index

    def list_files(
        self,
    ) -> list[str]:

        return [
            item.get(
                "path",
                "",
            )
            for item in self.index.files()
        ]

    def find_by_suffix(
        self,
        suffix: str,
    ) -> list[str]:

        if not suffix:
            return []

        return [
            item.get(
                "path",
                "",
            )
            for item in self.index.files()
            if item.get(
                "suffix"
            ) == suffix
        ]

    def find(
        self,
        keyword: str,
    ) -> list[dict[str, Any]]:

        if not keyword:
            return []

        return self.index.find_file(
            keyword
        )

    def ready(
        self,
    ) -> bool:

        return self.index is not None

    def dump(
        self,
    ) -> dict:

        return {
            "name":
                "WorkspaceFileQuery",

            "version":
                self.VERSION,

            "ready":
                self.ready(),
        }


__all__ = [
    "WorkspaceFileQuery",
]
