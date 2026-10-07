from __future__ import annotations

from typing import Any

from backend.workspace.file_access import WorkspaceFileAccess
from backend.workspace.file_query import WorkspaceFileQuery


class FileRepository:
    """
    Workspace file repository.

    Responsibility:
        - repository abstraction
        - coordinate file access
        - coordinate indexed query

    Not Responsible:
        - scanning
        - indexing construction
        - analysis
        - lifecycle
    """

    VERSION = "2.1"

    def __init__(
        self,
        file_access: WorkspaceFileAccess,
        file_query: WorkspaceFileQuery,
    ) -> None:

        if file_access is None:
            raise ValueError(
                "file_access required"
            )

        if file_query is None:
            raise ValueError(
                "file_query required"
            )

        self.file_access = file_access
        self.file_query = file_query

    def read(
        self,
        path: str,
    ) -> str:

        return self.file_access.read_text(
            path
        )

    def write(
        self,
        path: str,
        content: str,
    ) -> None:

        self.file_access.write_text(
            path,
            content,
        )

    def exists(
        self,
        path: str,
    ) -> bool:

        return self.file_access.exists(
            path
        )

    def list_files(
        self,
    ) -> list[str]:

        return self.file_query.list_files()

    def find_files(
        self,
        suffix: str,
    ) -> list[str]:

        return self.file_query.find_by_suffix(
            suffix
        )

    def find(
        self,
        keyword: str,
    ) -> list[dict[str, Any]]:

        return self.file_query.find(
            keyword
        )

    def ready(
        self,
    ) -> bool:

        return (
            self.file_access is not None
            and self.file_query is not None
        )

    def dump(
        self,
    ) -> dict:

        return {
            "name":
                "FileRepository",

            "version":
                self.VERSION,

            "ready":
                self.ready(),
        }


__all__ = [
    "FileRepository",
]
