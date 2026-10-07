from __future__ import annotations

from dataclasses import dataclass

from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.lifecycle.state import (
    LifecycleState,
)


@dataclass(
    frozen=True,
)
class LifecycleEvent:
    """
    Lifecycle event model.

    Responsibility:
        - describe lifecycle transition

    Not Responsible:
        - event dispatch
        - event storage
        - component execution
    """

    component_id: str
    component_name: str
    state: LifecycleState

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "state": self.state.value,
        }


__all__ = [
    "LifecycleEvent",
]
