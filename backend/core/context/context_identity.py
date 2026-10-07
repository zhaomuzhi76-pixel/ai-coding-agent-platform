from __future__ import annotations

from dataclasses import dataclass

from backend.core.contracts.value import (
    CoreValue,
)


@dataclass(
    frozen=True,
)
class ContextIdentity:
    """
    Stable context identity.

    Owns:
        - context identifier

    Does not own:
        - metadata
        - runtime state
        - persistence
        - execution
    """

    VERSION = "1.0"

    context_id: str

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.context_id,
            str,
        ):
            raise TypeError(
                "context id must str"
            )

        normalized = self.context_id.strip()

        if not normalized:
            raise ValueError(
                "context id required"
            )

        object.__setattr__(
            self,
            "context_id",
            normalized,
        )

    def ready(
        self,
    ) -> bool:

        return bool(
            self.context_id
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "context_id": self.context_id,
            "ready": self.ready(),
        }


__all__ = [
    "ContextIdentity",
]
