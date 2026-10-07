from __future__ import annotations

from dataclasses import dataclass

from backend.core.contracts.value import (
    CoreValue,
    is_core_value,
)


@dataclass(frozen=True)
class Payload:

    value: CoreValue

    def __post_init__(self) -> None:
        if not is_core_value(
            self.value,
        ):
            raise TypeError(
                "invalid payload"
            )

    def dump(
        self,
    ) -> CoreValue:
        return self.value


__all__ = [
    "Payload",
]
