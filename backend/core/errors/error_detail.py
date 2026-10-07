from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping
from types import MappingProxyType

from backend.core.contracts.value import CoreValue
from backend.core.errors.error_code import (
    CoreErrorCode,
)


@dataclass(
    frozen=True,
    slots=True,
)
class CoreErrorDetail:
    """
    Canonical framework error value.

    Ownership:
        - store normalized error identity
        - store safe error message
        - store structured metadata

    Not Responsible:
        - exception handling
        - transport serialization
        - logging
        - lifecycle orchestration
        - business recovery policy
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "core_error_value",
        "core_error_metadata",
    )

    code: CoreErrorCode
    message: str
    metadata: Mapping[str, CoreValue] = field(
        default_factory=dict,
    )

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.code,
            CoreErrorCode,
        ):
            raise TypeError(
                "error code must CoreErrorCode"
            )

        if not isinstance(
            self.message,
            str,
        ) or not self.message.strip():

            raise ValueError(
                "error message required"
            )

        object.__setattr__(
            self,
            "message",
            self.message.strip(),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )

    def ready(
        self,
    ) -> bool:

        return bool(
            self.code
            and self.message
            and isinstance(
                self.metadata,
                Mapping,
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": "CoreErrorDetail",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "code": self.code.value,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "CoreErrorDetail",
]
