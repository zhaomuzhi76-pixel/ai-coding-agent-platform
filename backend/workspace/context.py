from __future__ import annotations

import os
from typing import Any


class WorkspaceContext:
    """
    Workspace runtime context.

    Responsibility:
        - workspace identity
        - workspace root path
        - opened file runtime state
        - workspace runtime metadata

    Not Responsible:
        - execution state
        - agent runtime
        - file scanning
        - indexing
        - persistence
        - LLM interaction
    """

    VERSION = "4.1"

    RESPONSIBILITY = "workspace_context"

    def __init__(
        self,
        root_path: str,
        workspace_id: str | None = None,
    ) -> None:

        self.workspace_id = workspace_id

        self.root_path = os.path.abspath(
            root_path
        )

        self._open_files: dict[str, str] = {}

        self._runtime_data: dict[str, Any] = {}

    def ready(
        self,
    ) -> bool:

        return bool(
            self.root_path
        )

    def set_runtime_data(
        self,
        key: str,
        value: Any,
    ) -> None:

        self._runtime_data[key] = value

    def get_runtime_data(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self._runtime_data.get(
            key,
            default,
        )

    def open_file(
        self,
        path: str,
        content: str,
    ) -> None:

        self._open_files[path] = content

    def get_file(
        self,
        path: str,
    ) -> str | None:

        return self._open_files.get(
            path
        )

    def list_open_files(
        self,
    ) -> list[str]:

        return list(
            self._open_files.keys()
        )

    def clear_open_files(
        self,
    ) -> None:

        self._open_files.clear()

    def get_root_path(
        self,
    ) -> str:

        return self.root_path

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name": "WorkspaceContext",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "workspace_id": self.workspace_id,
            "root_path": self.root_path,
            "open_files": dict(
                self._open_files
            ),
            "runtime_data": dict(
                self._runtime_data
            ),
        }


__all__ = [
    "WorkspaceContext",
]
