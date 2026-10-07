from __future__ import annotations

from typing import Final
from uuid import uuid4

from backend.core.contracts.timestamp import (
    now_timestamp,
)
from backend.core.contracts.value import (
    CoreValue,
)


class BaseComponent:
    """
    Canonical framework component foundation.

    Owns:
        - stable component identity
        - component role
        - capability declaration
        - creation/update timestamps
        - immutable snapshot generation

    Does not own:
        - lifecycle orchestration
        - health monitoring
        - dependency injection
        - persistence
        - business execution
    """

    VERSION: Final = "11.0"

    COMPONENT_TYPE: Final = (
        "component"
    )

    CAPABILITIES: Final[tuple[str, ...]] = ()

    def __init__(
        self,
        name: str = "component",
        *,
        component_type: str | None = None,
    ) -> None:
        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "component name must str"
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "component name required"
            )

        resolved_type = (
            component_type
            or self.COMPONENT_TYPE
        )

        if not isinstance(
            resolved_type,
            str,
        ):
            raise TypeError(
                "component type must str"
            )

        resolved_type = (
            resolved_type.strip()
        )

        if not resolved_type:
            raise ValueError(
                "component type required"
            )

        timestamp = now_timestamp()

        self._component_id = (
            f"cmp_{uuid4().hex}"
        )

        self._name = normalized_name

        self._component_type = (
            resolved_type
        )

        self._created_at = timestamp
        self._updated_at = timestamp

    @property
    def component_id(
        self,
    ) -> str:
        return self._component_id

    @property
    def name(
        self,
    ) -> str:
        return self._name

    @property
    def component_type(
        self,
    ) -> str:
        return self._component_type

    @property
    def created_at(
        self,
    ) -> str:
        return self._created_at

    @property
    def updated_at(
        self,
    ) -> str:
        return self._updated_at

    def capabilities(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            self.CAPABILITIES
        )

    def supports(
        self,
        capability: str,
    ) -> bool:
        if not isinstance(
            capability,
            str,
        ):
            raise TypeError(
                "capability must str"
            )

        return (
            capability.strip()
            in self.capabilities()
        )

    def touch(
        self,
    ) -> None:
        self._updated_at = (
            now_timestamp()
        )

    def ready(
        self,
    ) -> bool:
        return bool(
            self._component_id
            and self._name
            and self._component_type
        )

    def snapshot(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "id": self.component_id,
            "name": self.name,
            "type": self.component_type,
            "version": self.VERSION,
            "capabilities": list(
                self.capabilities()
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return dict(
            self.snapshot()
        )


__all__ = [
    "BaseComponent",
]
