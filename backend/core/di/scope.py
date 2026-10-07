from __future__ import annotations

from backend.core.di.value_protocol import (
    DependencyValueProtocol,
)


class DependencyScope:
    """
    Scoped instance storage.

    Owns:
        - scoped dependency instances

    Does not own:
        - dependency definitions
        - provider creation
        - lifecycle policy
    """

    VERSION = "2.1"


    def __init__(
        self,
        name: str,
    ) -> None:

        self._name = self._normalize_name(
            name
        )

        self._instances: dict[
            str,
            DependencyValueProtocol,
        ] = {}


    @property
    def name(
        self,
    ) -> str:
        return self._name


    def store(
        self,
        name: str,
        instance: DependencyValueProtocol,
    ) -> None:

        normalized = self._normalize_name(
            name
        )

        if instance is None:
            raise ValueError(
                "instance required"
            )

        self._instances[
            normalized
        ] = instance


    def get(
        self,
        name: str,
    ) -> DependencyValueProtocol:

        normalized = self._normalize_name(
            name
        )

        try:
            return self._instances[
                normalized
            ]

        except KeyError as error:
            raise KeyError(
                f"scope instance missing: {normalized}"
            ) from error


    def contains(
        self,
        name: str,
    ) -> bool:

        return (
            self._normalize_name(name)
            in self._instances
        )


    def clear(
        self,
    ) -> None:

        self._instances.clear()


    def names(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            self._instances
        )


    def ready(
        self,
    ) -> bool:

        return bool(
            self._name
            and isinstance(
                self._instances,
                dict,
            )
        )


    def dump(
        self,
    ) -> dict[str, str | bool | tuple[str, ...]]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "scope": self._name,
            "instances": list(self.names()),
            "ready": self.ready(),
        }


    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "scope name must str"
            )

        normalized = name.strip()

        if not normalized:
            raise ValueError(
                "scope name required"
            )

        return normalized


__all__ = [
    "DependencyScope",
]
