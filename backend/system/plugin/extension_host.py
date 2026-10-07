from __future__ import annotations
from backend.core.observability.silent import swallow

from collections.abc import Iterable

from backend.system.contracts.system_contract import (
    SystemExtensionProtocol,
)


class SystemExtensionHost:
    """
    Host for system-level extensions.

    Owns extension attachment order and teardown.
    It does not discover, load, resolve, or execute plugins.
    """

    VERSION = "1.2"

    def __init__(
        self,
        extensions: Iterable[SystemExtensionProtocol] | None = None,
        context=None,
    ) -> None:
        self.context = context
        self._extensions: dict[
            str,
            SystemExtensionProtocol,
        ] = {}

        for extension in extensions or ():
            self.register(extension)

    def register(
        self,
        extension: SystemExtensionProtocol,
    ) -> None:
        self._validate(extension)

        if extension.name in self._extensions:
            raise ValueError(
                f"system extension already registered: "
                f"{extension.name}"
            )

        self._extensions[extension.name] = extension

    def attach_all(self) -> tuple[str, ...]:
        attached: list[SystemExtensionProtocol] = []
        names: list[str] = []

        try:
            for extension in self._extensions.values():
                attached.append(extension)

                extension.attach(self.context)

                if not extension.ready():
                    raise RuntimeError(
                        "system extension unavailable: "
                        f"{extension.name}"
                    )

                names.append(extension.name)

        except Exception:
            try:
                self._detach_attached(attached)
            except Exception as e:
                swallow("system.plugin.extension_host:71", e)
            raise

        return tuple(names)

    def detach_all(self) -> tuple[str, ...]:
        return self._detach_attached(
            tuple(self._extensions.values())
        )

    def ready(self) -> bool:
        return all(
            extension.ready()
            for extension in self._extensions.values()
        )

    def names(self) -> tuple[str, ...]:
        return tuple(self._extensions)

    def count(self) -> int:
        return len(self._extensions)

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "extensions": self.names(),
            "count": self.count(),
            "ready": self.ready(),
        }

    @classmethod
    def _detach_attached(
        cls,
        extensions: Iterable[SystemExtensionProtocol],
    ) -> tuple[str, ...]:
        detached: list[str] = []

        for extension in reversed(tuple(extensions)):
            try:
                extension.detach()
            finally:
                detached.append(extension.name)

        return tuple(detached)

    @staticmethod
    def _validate(
        extension: SystemExtensionProtocol,
    ) -> None:
        if extension is None:
            raise ValueError(
                "system extension required"
            )

        if not isinstance(
            extension.name,
            str,
        ) or not extension.name.strip():
            raise TypeError(
                "system extension name required"
            )

        if not callable(extension.attach):
            raise TypeError(
                "system extension attach() required"
            )

        if not callable(extension.detach):
            raise TypeError(
                "system extension detach() required"
            )

        if not callable(extension.ready):
            raise TypeError(
                "system extension ready() required"
            )


__all__ = [
    "SystemExtensionHost",
]
