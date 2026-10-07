from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Identifier:
    value: str

    def __post_init__(self) -> None:
        self._validate(
            self.value,
            "identifier",
        )

    def dump(self) -> str:
        return self.value

    @staticmethod
    def _validate(
        value: str,
        name: str,
    ) -> None:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be str"
            )

        if not value.strip():
            raise ValueError(
                f"{name} cannot be empty"
            )


@dataclass(frozen=True)
class SessionId:
    value: str

    def __post_init__(self) -> None:
        Identifier._validate(
            self.value,
            "session id",
        )

    def dump(self) -> str:
        return self.value


@dataclass(frozen=True)
class PluginId:
    value: str

    def __post_init__(self) -> None:
        Identifier._validate(
            self.value,
            "plugin id",
        )

    def dump(self) -> str:
        return self.value


@dataclass(frozen=True)
class ComponentId:
    value: str

    def __post_init__(self) -> None:
        Identifier._validate(
            self.value,
            "component id",
        )

    def dump(self) -> str:
        return self.value


__all__ = [
    "Identifier",
    "SessionId",
    "PluginId",
    "ComponentId",
]
