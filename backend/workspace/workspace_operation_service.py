from __future__ import annotations

from backend.workspace.context import WorkspaceContext
from backend.workspace.repository import FileRepository


class WorkspaceOperationService:
    """
    Workspace business service.

    Responsibility:
        - workspace file operations
        - coordinate repository access
        - synchronize workspace context

    Not Responsible:
        - filesystem implementation
        - path security
        - directory scanning
        - indexing
        - analysis
    """

    VERSION = "2.1"

    def __init__(
        self,
        context: WorkspaceContext,
        repository: FileRepository,
    ) -> None:

        if context is None:
            raise ValueError(
                "WorkspaceContext required"
            )

        if repository is None:
            raise ValueError(
                "FileRepository required"
            )

        self.context = context
        self.repository = repository

    def read_file(
        self,
        path: str,
    ) -> str:

        content = (
            self.repository
            .read(path)
        )

        self.context.open_file(
            path,
            content,
        )

        return content

    def write_file(
        self,
        path: str,
        content: str,
    ) -> None:

        self.repository.write(
            path,
            content,
        )

        self.context.open_file(
            path,
            content,
        )

    def edit_file(
        self,
        path: str,
        old_text: str,
        new_text: str,
    ) -> dict:

        if not path:
            raise ValueError(
                "path required"
            )

        if old_text is None:
            raise ValueError(
                "old_text required"
            )

        if new_text is None:
            raise ValueError(
                "new_text required"
            )

        content = (
            self.repository
            .read(path)
        )

        matches = content.count(
            old_text
        )

        if matches == 0:
            raise ValueError(
                "target content not found"
            )

        updated = self._replace_once(
            content,
            old_text,
            new_text,
        )

        self.repository.write(
            path,
            updated,
        )

        self.context.open_file(
            path,
            updated,
        )

        return {
            "path": path,
            "replaced": 1,
            "matches": matches,
        }

    def _replace_once(
        self,
        content: str,
        old_text: str,
        new_text: str,
    ) -> str:

        return content.replace(
            old_text,
            new_text,
            1,
        )

    def exists(
        self,
        path: str,
    ) -> bool:

        return self.repository.exists(
            path
        )

    def ready(
        self,
    ) -> bool:

        return (
            self.context is not None
            and self.repository is not None
            and self.repository.ready()
        )

    def dump(
        self,
    ) -> dict:

        return {
            "name":
                "WorkspaceOperationService",
            "version":
                self.VERSION,
            "ready":
                self.ready(),
        }


__all__ = [
    "WorkspaceOperationService",
]
