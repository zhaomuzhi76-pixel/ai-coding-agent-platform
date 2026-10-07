from __future__ import annotations


class WorkspaceRuntimeState:
    """
    Workspace runtime lifecycle state.

    Responsibility:
        - track workspace runtime lifecycle

    Not Responsible:
        - workspace loading
        - file operation
        - indexing
        - analysis
    """

    VERSION = "2.0"

    STATUS_CLOSED = "closed"
    STATUS_OPENED = "opened"

    def __init__(
        self,
    ) -> None:

        self.status = (
            self.STATUS_CLOSED
        )

        self.root_path = None

    def open(
        self,
        root_path: str,
    ) -> None:

        self.root_path = root_path
        self.status = (
            self.STATUS_OPENED
        )

    def close(
        self,
    ) -> None:

        self.status = (
            self.STATUS_CLOSED
        )

        self.root_path = None

    def ready(
        self,
    ) -> bool:

        return (
            self.status
            == self.STATUS_OPENED
            and bool(
                self.root_path
            )
        )

    def is_open(
        self,
    ) -> bool:

        return self.status == self.STATUS_OPENED

    def dump(
        self,
    ) -> dict:

        return {
            "name": "WorkspaceRuntimeState",
            "version": self.VERSION,
            "ready": self.ready(),
            "status": self.status,
            "root_path": self.root_path,
        }


__all__ = [
    "WorkspaceRuntimeState",
]
