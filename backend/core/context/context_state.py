from __future__ import annotations

from copy import deepcopy

from backend.core.contracts.value import (
    CoreValue,
)


class ContextState:
    """
    Mutable context value state.

    Owns:
        - runtime values
        - snapshot
        - restore
        - freeze boundary

    Does not own:
        - identity
        - metadata
        - lifecycle
        - execution
    """

    VERSION = "1.0"

    def __init__(
        self,
    ) -> None:
        self._values: dict[
            str,
            CoreValue,
        ] = {}

        self._frozen = False

    def set(
        self,
        key: str,
        value: CoreValue,
    ) -> None:

        self._ensure_mutable()

        self._values[
            self._normalize_key(key)
        ] = value


    def get(
        self,
        key: str,
    ) -> CoreValue | None:

        return self._values.get(
            self._normalize_key(key)
        )


    def contains(
        self,
        key: str,
    ) -> bool:

        return (
            self._normalize_key(key)
            in self._values
        )


    def freeze(
        self,
    ) -> None:

        self._frozen = True


    def snapshot(
        self,
    ) -> dict[str, CoreValue]:

        return deepcopy(
            self._values
        )


    def restore(
        self,
        snapshot: dict[str, CoreValue],
    ) -> None:

        self._ensure_mutable()

        if not isinstance(
            snapshot,
            dict,
        ):
            raise TypeError(
                "snapshot must dict"
            )

        self._values = deepcopy(
            snapshot
        )


    def ready(
        self,
    ) -> bool:

        return isinstance(
            self._values,
            dict,
        )


    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "frozen": self._frozen,
            "state": self.snapshot(),
        }


    def frozen(
        self,
    ) -> bool:

        return self._frozen


    def _ensure_mutable(
        self,
    ) -> None:

        if self._frozen:
            raise RuntimeError(
                "context state frozen"
            )


    @staticmethod
    def _normalize_key(
        key: str,
    ) -> str:

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "context key must str"
            )

        value = key.strip()

        if not value:
            raise ValueError(
                "context key required"
            )

        return value


__all__ = [
    "ContextState",
]
