from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.ready import ReadyProtocol
from backend.runtime.bootstrap.runtime_plugin_access import (
    RuntimePluginProviderAccessProtocol,
)
from backend.runtime.plugin.capability import RuntimeCapability


@runtime_checkable
class RuntimeCapabilityCreatorProtocol(Protocol):
    def create(self) -> object:
        ...


@runtime_checkable
class RuntimeKnowledgeCapabilityCreatorProtocol(Protocol):
    def create_middleware(self) -> object:
        ...


class RuntimeSemanticCapabilityAccess:
    """
    Runtime semantic capability access boundary.

    Generic capability discovery stays internal.
    Application receives named semantic creation operations.
    """

    VERSION = "2.2"

    def __init__(
        self,
        *,
        plugin_provider: RuntimePluginProviderAccessProtocol,
    ) -> None:
        if not isinstance(
            plugin_provider,
            RuntimePluginProviderAccessProtocol,
        ):
            raise TypeError(
                "plugin provider access contract required"
            )
        if not plugin_provider.ready():
            raise RuntimeError(
                "plugin provider unavailable"
            )

        self.plugin_provider = plugin_provider

    def create_knowledge_middleware(self) -> object:
        provider = self._resolve(
            "knowledge.runtime"
        )

        if not isinstance(
            provider,
            RuntimeKnowledgeCapabilityCreatorProtocol,
        ):
            raise TypeError(
                "knowledge capability creator contract required"
            )

        value = provider.create_middleware()
        return self._require_ready(
            value,
            "knowledge runtime",
        )

    def create_code_intelligence_capability(
        self,
    ) -> object:
        return self._create(
            "code_intelligence.inspect",
            "code intelligence",
        )

    def create_code_modification_provider(
        self,
    ) -> object:
        return self._create(
            "code_modification.execute",
            "code modification",
        )

    def ready(self) -> bool:
        return self.plugin_provider.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    def _create(
        self,
        capability: str,
        label: str,
    ) -> object:
        provider = self._resolve(capability)

        if not isinstance(
            provider,
            RuntimeCapabilityCreatorProtocol,
        ):
            raise TypeError(
                f"{label} capability creator contract required"
            )

        value = provider.create()

        return self._require_ready(
            value,
            label,
        )

    def _resolve(
        self,
        capability: str,
    ) -> object:
        category, name = self._split_capability(
            capability
        )

        return self.plugin_provider.resolve_capability(
            RuntimeCapability(
                category=category,
                name=name,
                version="1.0",
            )
        )

    @staticmethod
    def _require_ready(
        value: object,
        label: str,
    ) -> object:
        if not isinstance(
            value,
            ReadyProtocol,
        ):
            raise TypeError(
                f"{label} capability result must "
                "implement ReadyProtocol"
            )

        if not value.ready():
            raise RuntimeError(
                f"{label} capability unavailable"
            )

        return value

    @staticmethod
    def _split_capability(
        capability: str,
    ) -> tuple[str, str]:
        if not isinstance(
            capability,
            str,
        ) or "." not in capability:
            raise ValueError(
                "capability must category.name"
            )

        category, name = capability.split(
            ".",
            1,
        )

        if not category.strip() or not name.strip():
            raise ValueError(
                "capability category and name required"
            )

        return category.strip(), name.strip()


__all__ = [
    "RuntimeCapabilityCreatorProtocol",
    "RuntimeKnowledgeCapabilityCreatorProtocol",
    "RuntimeSemanticCapabilityAccess",
]
