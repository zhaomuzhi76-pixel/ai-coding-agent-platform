from __future__ import annotations

from collections import defaultdict

from backend.runtime.plugin.capability import RuntimeCapability


class RuntimeCapabilityRegistry:
    """
    Runtime capability registry.

    Responsibility:
        - register capabilities
        - resolve capability providers
        - define canonical version selection

    Not Responsible:
        - plugin lifecycle
        - provider implementation
        - execution orchestration
    """

    VERSION = "2.3"

    def __init__(self) -> None:
        self._items: dict[
            str,
            dict[str, object],
        ] = defaultdict(dict)

    def register(
        self,
        capability: RuntimeCapability,
        provider: object,
    ) -> None:
        if not isinstance(
            capability,
            RuntimeCapability,
        ):
            raise TypeError(
                "invalid capability"
            )

        if provider is None:
            raise ValueError(
                "capability provider required"
            )

        versions = self._items[
            capability.key()
        ]

        if capability.version in versions:
            raise ValueError(
                "capability already registered: "
                f"{capability.key()}:{capability.version}"
            )

        versions[capability.version] = provider

    def resolve(
        self,
        capability: RuntimeCapability | str,
        version: str | None = None,
    ) -> object:
        key = self._key(capability)
        target_version = self._version(
            capability,
            version,
        )

        try:
            return self._items[
                key
            ][
                target_version
            ]
        except KeyError as error:
            raise LookupError(
                "capability not found: "
                f"{key}:{target_version}"
            ) from error

    def exists(
        self,
        capability: RuntimeCapability | str,
        version: str | None = None,
    ) -> bool:
        key = self._key(capability)
        versions = self._items.get(
            key,
        )

        if not versions:
            return False

        if version is not None:
            return version in versions

        if isinstance(
            capability,
            RuntimeCapability,
        ):
            return capability.version in versions

        return True

    def list(
        self,
    ) -> dict[str, tuple[str, ...]]:
        return {
            key: tuple(
                versions.keys()
            )
            for key, versions in self._items.items()
        }

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "capabilities": self.list(),
            "ready": self.ready(),
        }

    def _key(
        self,
        capability: RuntimeCapability | str,
    ) -> str:
        if isinstance(
            capability,
            RuntimeCapability,
        ):
            return capability.key()

        if not capability:
            raise ValueError(
                "capability required"
            )

        return capability

    def _version(
        self,
        capability: RuntimeCapability | str,
        version: str | None,
    ) -> str:
        if version:
            return version

        if isinstance(
            capability,
            RuntimeCapability,
        ):
            return capability.version

        versions = self._items.get(
            capability,
            {},
        )

        if not versions:
            raise LookupError(
                "capability not registered: "
                f"{capability}"
            )

        return self._canonical_version(
            versions
        )

    @staticmethod
    def _canonical_version(
        versions: dict[str, object],
    ) -> str:
        return max(
            versions,
            key=RuntimeCapabilityRegistry._version_key,
        )

    @staticmethod
    def _version_key(
        version: str,
    ) -> tuple[int, ...]:
        values: list[int] = []

        for part in version.split("."):
            try:
                values.append(
                    int(part)
                )
            except ValueError:
                values.append(0)

        return tuple(values)


__all__ = [
    "RuntimeCapabilityRegistry",
]
