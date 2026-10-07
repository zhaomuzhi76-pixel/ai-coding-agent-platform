from __future__ import annotations

from dataclasses import dataclass

from backend.registry.contracts import RegistryEntryProtocol


@dataclass(frozen=True)
class RegistryRecord:
    """
    Unified registry metadata record.
    """

    category: str
    name: str
    version: str
    item: RegistryEntryProtocol

    def __post_init__(self) -> None:
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("registry category required")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("registry name required")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("registry version required")
        if not isinstance(self.item, RegistryEntryProtocol):
            raise TypeError(
                "registry item must implement RegistryEntryProtocol"
            )

    def ready(self) -> bool:
        return self.item.ready()

    def dump(self) -> dict[str, object]:
        return {
            "category": self.category,
            "name": self.name,
            "version": self.version,
            "type": type(self.item).__name__,
            "ready": self.ready(),
        }


class RegistryCatalog:
    """
    Unified framework registry catalog.

    Stores metadata and object references without replacing
    ownership of the underlying subsystem registries.
    """

    VERSION = "1.1"

    def __init__(self) -> None:
        self._records: dict[
            str,
            dict[str, RegistryRecord],
        ] = {}

    def add(self, record: RegistryRecord) -> None:
        if not isinstance(record, RegistryRecord):
            raise TypeError("registry record required")

        bucket = self._records.setdefault(
            record.category,
            {},
        )

        if record.name in bucket:
            raise ValueError(
                "registry record already exists: "
                f"{record.category}/{record.name}"
            )

        bucket[record.name] = record

    def get(
        self,
        category: str,
        name: str,
    ) -> RegistryRecord:
        try:
            return self._records[
                category
            ][name]
        except KeyError as error:
            raise LookupError(
                f"registry record not found: "
                f"{category}/{name}"
            ) from error

    def exists(
        self,
        category: str,
        name: str,
    ) -> bool:
        return (
            category in self._records
            and name in self._records[category]
        )

    def categories(self) -> tuple[str, ...]:
        return tuple(self._records)

    def names(
        self,
        category: str | None = None,
    ) -> tuple[str, ...]:
        if category is not None:
            return tuple(
                self._records.get(
                    category,
                    {},
                )
            )

        return tuple(
            f"{category}/{name}"
            for category, records
            in self._records.items()
            for name in records
        )

    def ready(self) -> bool:
        return all(
            record.ready()
            for records in self._records.values()
            for record in records.values()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "categories": self.categories(),
            "records": self.names(),
            "ready": self.ready(),
        }


__all__ = [
    "RegistryRecord",
    "RegistryCatalog",
]
