from __future__ import annotations

from backend.core.context.execution_context_storage_protocol import (
    ExecutionContextStorageProtocol,
)

from backend.core.context.execution_storage_contract import (
    ExecutionContextStorageSnapshot,
)

from backend.core.context.storage_component_protocol import (
    StorageComponentProtocol,
)


class ExecutionContextStorage:
    """
    Execution storage composition root.

    Responsibility:

        - compose execution storage components
        - expose storage readiness
        - clear composed storage
        - expose storage snapshot

    Not Responsible:

        - variable management
        - output management
        - artifact management
        - persistence
        - lifecycle
        - scheduling
        - execution logic
    """

    VERSION = "5.0"

    RESPONSIBILITY = (
        "execution_storage_composition",
    )

    def __init__(
        self,
        variable_store: StorageComponentProtocol,
        output_store: StorageComponentProtocol,
    ) -> None:

        if not isinstance(
            variable_store,
            StorageComponentProtocol,
        ):
            raise TypeError(
                "variable_store must implement StorageComponentProtocol"
            )

        if not isinstance(
            output_store,
            StorageComponentProtocol,
        ):
            raise TypeError(
                "output_store must implement StorageComponentProtocol"
            )

        self.variable_store = variable_store
        self.output_store = output_store

    def ready(
        self,
    ) -> bool:

        return (
            self.variable_store.ready()
            and self.output_store.ready()
        )

    def clear(
        self,
    ) -> None:

        self.variable_store.clear()
        self.output_store.clear()

    def dump(
        self,
    ) -> ExecutionContextStorageSnapshot:

        return {
            "name": "ExecutionContextStorage",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "variable_store":
                self.variable_store.dump(),
            "output_store":
                self.output_store.dump(),
        }


__all__ = [
    "ExecutionContextStorage",
]
