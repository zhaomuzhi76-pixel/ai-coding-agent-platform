from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.contracts.value import CoreValue


@dataclass(frozen=True)
class RuntimeExecutionStep:
    """
    Core-owned runtime-neutral execution step contract.

    Responsibility:
        - carry executable node identity
        - carry executor type and parameters
        - carry dependency and metadata payloads

    Not Responsible:
        - planning
        - runtime execution
        - scheduling
        - lifecycle
        - persistence
    """

    VERSION = "1.2"

    node_id: str
    executor_type: str
    node_type: str = ""
    description: str = ""

    depends_on: list[str] = field(
        default_factory=list
    )

    parameters: dict[str, CoreValue] = field(
        default_factory=dict
    )

    metadata: dict[str, CoreValue] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.node_id, str)
            or not self.node_id.strip()
        ):
            raise ValueError("node_id required")

        if (
            not isinstance(self.executor_type, str)
            or not self.executor_type.strip()
        ):
            raise ValueError("executor_type required")

        object.__setattr__(
            self,
            "node_type",
            self.node_type or self.executor_type,
        )
        object.__setattr__(
            self,
            "depends_on",
            list(self.depends_on),
        )
        object.__setattr__(
            self,
            "parameters",
            dict(self.parameters),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


__all__ = [
    "RuntimeExecutionStep",
]
