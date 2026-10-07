from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.planning.step_protocol import (
    PlanningStepProtocol,
)


@dataclass(frozen=True)
class PlanningRequest:
    """
    Core-owned stable planning request.
    """

    message: str
    workspace: str = "."
    model: str = ""
    metadata: dict[str, CoreValue] = field(
        default_factory=dict
    )

    def ready(self) -> bool:
        return (
            isinstance(self.message, str)
            and bool(self.message.strip())
            and isinstance(self.workspace, str)
            and bool(self.workspace.strip())
            and all(
                isinstance(key, str)
                and _is_core_value(value)
                for key, value in self.metadata.items()
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "message": self.message,
            "workspace": self.workspace,
            "model": self.model,
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


@dataclass(frozen=True)
class PlanningResult:
    """
    Core-owned stable planning result.

    Steps remain domain objects behind PlanningStepProtocol.
    """

    steps: tuple[PlanningStepProtocol, ...]
    metadata: dict[str, CoreValue] = field(
        default_factory=dict
    )

    def ready(self) -> bool:
        return (
            isinstance(self.steps, tuple)
            and all(
                isinstance(
                    step,
                    PlanningStepProtocol,
                )
                for step in self.steps
            )
            and all(
                isinstance(key, str)
                and _is_core_value(value)
                for key, value in self.metadata.items()
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "steps": [
                _dump_step(step)
                for step in self.steps
            ],
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


@runtime_checkable
class PlanningCapabilityProtocol(
    Protocol,
):
    async def plan(
        self,
        request: PlanningRequest,
    ) -> PlanningResult:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


def _is_core_value(
    value: CoreValue,
) -> bool:
    if value is None:
        return True

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return True

    if isinstance(value, list):
        return all(
            _is_core_value(item)
            for item in value
        )

    if isinstance(value, dict):
        return all(
            isinstance(key, str)
            and _is_core_value(item)
            for key, item in value.items()
        )

    return False


def _dump_step(
    step: PlanningStepProtocol,
) -> dict[str, CoreValue]:
    return {
        "node_id": step.node_id,
        "executor_type": step.executor_type,
        "node_type": step.node_type,
        "description": step.description,
        "depends_on": list(step.depends_on),
        "parameters": dict(step.parameters),
        "metadata": dict(step.metadata),
    }


__all__ = [
    "PlanningCapabilityProtocol",
    "PlanningRequest",
    "PlanningResult",
]
