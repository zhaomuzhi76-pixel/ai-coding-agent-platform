from __future__ import annotations

from backend.core.context.context_access_protocol import (
    ContextAccessProtocol,
)
from backend.core.context.context_identity import ContextIdentity
from backend.core.context.context_metadata import ContextMetadata
from backend.core.context.execution_context_storage_protocol import (
    ExecutionContextStorageProtocol,
)
from backend.core.context.execution_output import ExecutionOutput
from backend.core.context.execution_variable import ExecutionVariable
from backend.core.context.runtime_context_contract import (
    RuntimeContextSnapshot,
)

from backend.core.contracts.timestamp import (
    now_timestamp,
)


class RuntimeContext(ContextAccessProtocol):
    """
    Canonical runtime context composition root.

    Owns canonical identity, storage and metadata.
    Exposes controlled context access and snapshot operations.

    Not responsible for runtime lifecycle state, persistence,
    transport, scheduling or execution.
    """

    VERSION = "24.0"

    RESPONSIBILITY = (
        "runtime_context_composition",
        "canonical_context_access",
    )

    def __init__(
        self,
        storage: ExecutionContextStorageProtocol,
        metadata: ContextMetadata,
        request_id: str | None = None,
        workspace_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        if not isinstance(
            storage,
            ExecutionContextStorageProtocol,
        ):
            raise TypeError(
                "storage must implement "
                "ExecutionContextStorageProtocol"
            )

        if not isinstance(
            metadata,
            ContextMetadata,
        ):
            raise TypeError(
                "metadata must be ContextMetadata"
            )

        if getattr(
            storage,
            "variable_store",
            None,
        ) is None:
            raise TypeError(
                "runtime variable store unavailable"
            )

        if getattr(
            storage,
            "output_store",
            None,
        ) is None:
            raise TypeError(
                "runtime output store unavailable"
            )

        self.identity = ContextIdentity(
            context_id=(
                request_id
                if request_id
                else "runtime_context"
            ),
        )

        self._workspace_id = workspace_id
        self._user_id = user_id

        self.storage = storage
        self.metadata = metadata

    @property
    def request_id(
        self,
    ) -> str:
        return self.identity.context_id

    @property
    def trace_id(
        self,
    ) -> str:
        return self.identity.context_id

    @property
    def workspace_id(
        self,
    ) -> str | None:
        return self._workspace_id

    @property
    def user_id(
        self,
    ) -> str | None:
        return self._user_id

    @property
    def created_at(
        self,
    ) -> str:
        if not hasattr(
            self,
            "_created_at",
        ):
            self._created_at = now_timestamp()

        return self._created_at

    def get_variable(
        self,
        name: str,
    ) -> ExecutionVariable | None:
        return self.storage.variable_store.get(name)

    def set_variable(
        self,
        variable: ExecutionVariable,
    ) -> None:
        self.storage.variable_store.add(
            variable
        )

    def remove_variable(
        self,
        name: str,
    ) -> None:
        self.storage.variable_store.remove(
            name
        )

    def variable_names(
        self,
    ) -> tuple[str, ...]:
        return self.storage.variable_store.names()

    def get_output(
        self,
        name: str,
    ) -> ExecutionOutput | None:
        return self.storage.output_store.get(
            name
        )

    def set_output(
        self,
        output: ExecutionOutput,
    ) -> None:
        self.storage.output_store.add(
            output
        )

    def remove_output(
        self,
        name: str,
    ) -> None:
        self.storage.output_store.remove(
            name
        )

    def output_names(
        self,
    ) -> tuple[str, ...]:
        return self.storage.output_store.names()

    def ready(
        self,
    ) -> bool:
        return (
            self.identity.ready()
            and self.storage.ready()
            and self.metadata.ready()
        )

    def clear(
        self,
    ) -> None:
        self.storage.clear()
        self.metadata.clear()

    def dump(
        self,
    ) -> RuntimeContextSnapshot:
        return {
            "name": "RuntimeContext",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "identity": self.identity.dump(),
            "storage": self.storage.dump(),
            "metadata": self.metadata.dump(),
        }


__all__ = [
    "RuntimeContext",
]
