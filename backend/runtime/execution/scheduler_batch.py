from __future__ import annotations

from dataclasses import dataclass, field


from backend.core.execution import (
    ExecutionNodeProtocol,
)


@dataclass(frozen=True)
class SchedulerBatch:
    """
    Runtime scheduler execution batch.

    Responsibility:
        - carry selected executable nodes
        - represent one scheduler dispatch unit

    Not Responsible:
        - node execution
        - scheduling decision
        - lifecycle mutation
        - retry handling
        - persistence
    """

    VERSION = "1.0"

    nodes: tuple[ExecutionNodeProtocol, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(
        self,
    ) -> None:

        for node in self.nodes:

            if not isinstance(
                node,
                ExecutionNodeProtocol,
            ):
                raise TypeError(
                    "batch nodes must ExecutionNodeProtocol"
                )

    @property
    def empty(
        self,
    ) -> bool:

        return len(
            self.nodes
        ) == 0

    def node_ids(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            node.node_id
            for node in self.nodes
        )

    def size(
        self,
    ) -> int:

        return len(
            self.nodes
        )

    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": "SchedulerBatch",
            "version": self.VERSION,
            "size": self.size(),
            "node_ids": self.node_ids(),
        }


__all__ = [
    "SchedulerBatch",
]
