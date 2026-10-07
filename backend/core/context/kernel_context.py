from __future__ import annotations

from typing import Any

from backend.core.context.context_state_protocol import (
    ContextStateProtocol,
)
from backend.core.context.kernel_metadata_carrier import (
    KernelMetadataCarrier,
)

from backend.core.context.context_access_protocol import ContextAccessProtocol
from backend.core.context.execution_output import ExecutionOutput
from backend.core.context.execution_variable import ExecutionVariable
from backend.core.context.kernel_output_payload import KernelOutputPayload


class KernelContext:
    """
    Core-owned request-scoped kernel execution context.

    Owns only context identity, lifecycle carrier, controlled
    variables/outputs and request-scoped metadata.
    """

    VERSION = "1.1"
    RESPONSIBILITY = (
        "kernel_execution_context",
        "kernel_lifecycle_state_carrier",
    )

    def __init__(
        self,
        runtime_context: ContextAccessProtocol,
        lifecycle_state: ContextStateProtocol,
        session_id: str,
    ) -> None:
        self._validate_runtime_context(runtime_context)
        self._validate_lifecycle_state(lifecycle_state)
        self._validate_session_id(session_id)

        self.runtime_context = runtime_context
        self.lifecycle_state = lifecycle_state
        self.session_id = session_id.strip()
        self.phase = "created"
        self.metadata = KernelMetadataCarrier()

    @classmethod
    def create(
        cls,
        runtime_context: ContextAccessProtocol,
        lifecycle_state: ContextStateProtocol,
        session_id: str,
    ) -> "KernelContext":
        return cls(
            runtime_context,
            lifecycle_state,
            session_id,
        )

    @property
    def request_id(self) -> str:
        return self.runtime_context.request_id

    @property
    def trace_id(self) -> str:
        return self.runtime_context.trace_id

    @property
    def workspace_id(self) -> str | None:
        return self.runtime_context.workspace_id

    @property
    def user_id(self) -> str | None:
        return self.runtime_context.user_id

    @property
    def created_at(self) -> str:
        return self.runtime_context.created_at

    @property
    def variables(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in self.runtime_context.variable_names():
            variable = self.runtime_context.get_variable(name)
            if variable is not None:
                result[name] = variable.value
        return result

    @property
    def outputs(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in self.runtime_context.output_names():
            output = self.runtime_context.get_output(name)
            if output is not None:
                result[name] = output.payload_snapshot.get("value")
        return result

    def set_phase(self, phase: str) -> None:
        self._require_key(phase, "phase required")
        self.phase = phase.strip()

    def set(self, key: str, value: Any) -> None:
        self._require_key(key, "context key required")

        if self.runtime_context.get_variable(key) is not None:
            self.runtime_context.remove_variable(key)

        self.runtime_context.set_variable(
            ExecutionVariable(
                name=key,
                value=value,
            )
        )

    def get(self, key: str, default: Any = None) -> Any:
        self._require_key(key, "context key required")
        variable = self.runtime_context.get_variable(key)
        return default if variable is None else variable.value

    def set_output(self, node_id: str, output: Any) -> None:
        self._require_key(node_id, "context key required")

        if self.runtime_context.get_output(node_id) is not None:
            self.runtime_context.remove_output(node_id)

        self.runtime_context.set_output(
            ExecutionOutput(
                name=node_id,
                payload=KernelOutputPayload(output),
            )
        )

    def get_output(
        self,
        node_id: str,
        default: Any = None,
    ) -> Any:
        self._require_key(node_id, "context key required")
        output = self.runtime_context.get_output(node_id)

        if output is None:
            return default

        return output.payload_snapshot.get("value", default)
    def ready(self) -> bool:
        return all(
            (
                self.runtime_context.ready(),
                self.lifecycle_state.ready(),
                bool(self.session_id),
                bool(self.request_id),
                bool(self.trace_id),
            )
        )

    def clear(self) -> None:
        self.metadata.clear()
        self.runtime_context.clear()
        self.phase = "created"

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": list(self.RESPONSIBILITY),
            "ready": self.ready(),
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "phase": self.phase,
            "metadata": self.metadata.dump(),
            "lifecycle_state": self.lifecycle_state.dump(),
            "runtime_context": self.runtime_context.dump(),
        }

    @staticmethod
    def _validate_runtime_context(
        runtime_context: ContextAccessProtocol,
    ) -> None:
        if not isinstance(runtime_context, ContextAccessProtocol):
            raise TypeError(
                "runtime_context must implement ContextAccessProtocol"
            )

    @staticmethod
    def _validate_lifecycle_state(
        lifecycle_state: ContextStateProtocol,
    ) -> None:
        if lifecycle_state is None:
            raise ValueError("lifecycle_state required")

        if not callable(getattr(lifecycle_state, "ready", None)):
            raise TypeError("lifecycle_state must expose ready()")

        if not callable(getattr(lifecycle_state, "dump", None)):
            raise TypeError("lifecycle_state must expose dump()")

    @staticmethod
    def _validate_session_id(session_id: str) -> None:
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session id required")

    @staticmethod
    def _require_key(value: Any, error: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(error)


__all__ = ["KernelContext"]
