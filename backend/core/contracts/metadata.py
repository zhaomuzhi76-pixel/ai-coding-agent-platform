from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from backend.core.contracts.value import (
    CoreValue,
    is_core_value,
)


@dataclass(frozen=True)
class Metadata:

    _values: Mapping[str, CoreValue]

    def __init__(
        self,
        values: dict[str, CoreValue] | None = None,
    ) -> None:

        source = values or {}

        if not isinstance(
            source,
            dict,
        ):
            raise TypeError(
                "metadata must be dict"
            )

        for key, value in source.items():

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    "metadata key invalid"
                )

            if not is_core_value(
                value,
            ):
                raise TypeError(
                    "metadata value invalid"
                )

        object.__setattr__(
            self,
            "_values",
            MappingProxyType(
                dict(source)
            ),
        )

    @property
    def values(
        self,
    ) -> Mapping[str, CoreValue]:
        return self._values

    def get(
        self,
        key: str,
        default: CoreValue = None,
    ) -> CoreValue:
        return self._values.get(
            key,
            default,
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return dict(
            self._values
        )


__all__ = [
    "Metadata",
]
