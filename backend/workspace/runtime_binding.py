from __future__ import annotations

from backend.workspace.context import (
    WorkspaceContext,
)
from backend.workspace.file_access import (
    WorkspaceFileAccess,
)
from backend.workspace.file_query import (
    WorkspaceFileQuery,
)
from backend.workspace.repository import (
    FileRepository,
)
from backend.workspace.workspace_index import (
    WorkspaceIndex,
)
from backend.workspace.workspace_index_builder import (
    WorkspaceIndexBuilder,
)
from backend.workspace.workspace_operation_service import (
    WorkspaceOperationService,
)
from backend.workspace.workspace_scanner import (
    WorkspaceScanner,
)


class WorkspaceRuntimeBinding:
    """
    Workspace runtime dependency binding.

    Responsibility:
        - compose workspace dependencies
        - construct initial workspace index
        - expose workspace components

    Not Responsible:
        - dependency registration
        - workspace lifecycle
        - query semantics
        - filesystem implementation
        - analysis
    """

    VERSION = "9.0"
    RESPONSIBILITY = (
        "workspace_runtime_binding",
    )

    def __init__(
        self,
        root_path: str,
        index: WorkspaceIndex | None = None,
    ) -> None:
        if not isinstance(
            root_path,
            str,
        ) or not root_path.strip():
            raise ValueError(
                "workspace root path required"
            )

        self.context = WorkspaceContext(
            root_path=root_path,
        )

        self.index = (
            index
            or WorkspaceIndex()
        )

        self.scanner = WorkspaceScanner(
            self.context.root_path
        )

        self.index_builder = (
            WorkspaceIndexBuilder(
                scanner=self.scanner,
                index=self.index,
            )
        )

        self.index_builder.build()

        self.query = WorkspaceFileQuery(
            self.index,
        )

        self.file_access = WorkspaceFileAccess(
            self.context.root_path,
        )

        self.repository = FileRepository(
            self.file_access,
            self.query,
        )

        self.service = WorkspaceOperationService(
            self.context,
            self.repository,
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.context.ready()
            and self.scanner.ready()
            and self.index.ready()
            and self.index_builder.ready()
            and self.file_access.ready()
            and self.query.ready()
            and self.repository.ready()
            and self.service.ready()
        )

    def get_context(
        self,
    ) -> WorkspaceContext:
        return self.context

    def get_service(
        self,
    ) -> WorkspaceOperationService:
        return self.service

    def get_filesystem(
        self,
    ) -> WorkspaceFileAccess:
        return self.file_access

    def get_operations(
        self,
    ) -> WorkspaceOperationService:
        return self.service

    def get_repository(
        self,
    ) -> FileRepository:
        return self.repository

    def get_index(
        self,
    ) -> WorkspaceIndex:
        return self.index

    def get_query(
        self,
    ) -> WorkspaceFileQuery:
        return self.query

    def get_scanner(
        self,
    ) -> WorkspaceScanner:
        return self.scanner

    def get_index_builder(
        self,
    ) -> WorkspaceIndexBuilder:
        return self.index_builder

    def dump(
        self,
    ) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "context": self.context.dump(),
            "scanner": self.scanner.dump(),
            "index_builder": self.index_builder.dump(),
            "index": self.index.dump(),
            "file_access": self.file_access.dump(),
            "repository": self.repository.dump(),
            "query": self.query.dump(),
            "service": self.service.dump(),
        }


__all__ = [
    "WorkspaceRuntimeBinding",
]
