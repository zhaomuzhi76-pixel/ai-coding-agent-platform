from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Final
from uuid import uuid4

from backend.core.context.execution_variable_contract import (
    ExecutionVariableSnapshot,
)
from backend.core.contracts.value import CoreValue, is_core_value


_CST: Final = timezone(
    timedelta(hours=8),
)


@dataclass(
    frozen=True,
    slots=True,
)
class ExecutionVariable:
    """
    Execution variable entity.

    Responsibility:

        - variable identity
        - variable name
        - typed value reference
        - creation timestamp

    Not Responsible:

        - storage
        - persistence
        - lifecycle
        - business processing
    """

    VERSION = "2.1"

    RESPONSIBILITY = (
        "execution_variable_entity",
    )

    name: str
    value: CoreValue
    variable_id: str = ""
    created_at: str = ""

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.name,
            str,
        ) or not self.name.strip():

            raise ValueError(
                "variable name required"
            )

        object.__setattr__(
            self,
            "name",
            self.name.strip(),
        )

        if not is_core_value(
            self.value,
        ):
            raise TypeError(
                "execution variable value must CoreValue"
            )

        if not self.variable_id:

            object.__setattr__(
                self,
                "variable_id",
                f"var_{uuid4().hex}",
            )

        if not self.created_at:

            object.__setattr__(
                self,
                "created_at",
                datetime.now(
                    _CST
                ).isoformat(),
            )

    def ready(
        self,
    ) -> bool:

        return bool(
            self.variable_id
            and self.name
            and self.created_at
        )

    def dump(
        self,
    ) -> ExecutionVariableSnapshot:

        return {
            "id": self.variable_id,
            "name": self.name,
            "value": self.value,
            "created_at": self.created_at,
        }


__all__ = [
    "ExecutionVariable",
]
