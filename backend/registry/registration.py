from __future__ import annotations

from typing import Any

from backend.registry.catalog import (
    RegistryCatalog,
    RegistryRecord,
)
from backend.registry.contracts import (
    RegistryEntryProtocol,
    RegistryTargetProtocol,
)


class RegistrationCoordinator:
    """
    Unified registration coordination boundary.

    Owns:
        - registration validation
        - duplicate prevention
        - catalog synchronization
        - registration metrics

    Does not own:
        - subsystem registry storage
        - subsystem construction
        - lifecycle
    """

    VERSION = "1.1"

    def __init__(
        self,
        catalog: RegistryCatalog,
    ) -> None:
        if not isinstance(catalog, RegistryCatalog):
            raise TypeError(
                "catalog must RegistryCatalog"
            )
        self.catalog = catalog
        self.registration_count = 0

    def register(
        self,
        *,
        category: str,
        item: RegistryEntryProtocol,
        target_registry: RegistryTargetProtocol,
        name: str | None = None,
        version: str | None = None,
    ) -> RegistryRecord:
        if not isinstance(category, str) or not category.strip():
            raise ValueError("registry category required")
        if not isinstance(
            item,
            RegistryEntryProtocol,
        ):
            raise TypeError(
                "item must RegistryEntryProtocol"
            )
        if not isinstance(
            target_registry,
            RegistryTargetProtocol,
        ):
            raise TypeError(
                "target registry must RegistryTargetProtocol"
            )

        entry_name = (
            name.strip()
            if isinstance(name, str) and name.strip()
            else item.name
        )
        entry_version = (
            version.strip()
            if isinstance(version, str) and version.strip()
            else item.version
        )

        if not entry_name:
            raise ValueError(
                "registry item name required"
            )
        if not entry_version:
            raise ValueError(
                "registry item version required"
            )

        if self.catalog.exists(
            category,
            entry_name,
        ):
            raise ValueError(
                f"registry record already exists: "
                f"{category}/{entry_name}"
            )

        target_registry.register(item)

        record = RegistryRecord(
            category=category.strip(),
            name=entry_name,
            version=entry_version,
            item=item,
        )

        self.catalog.add(record)
        self.registration_count += 1
        return record

    def ready(self) -> bool:
        return self.catalog.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "registration_count": self.registration_count,
            "catalog": self.catalog.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "RegistrationCoordinator",
]
