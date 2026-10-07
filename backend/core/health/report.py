from __future__ import annotations

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.health.status import (
    HealthStatus,
)


class HealthReport:
    """
    Immutable health report value.

    Owns:
        - component health status
        - message
        - metadata

    Does not own:
        - health execution
        - recovery
        - monitoring
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        name: str,
        status: HealthStatus,
        message: str = "",
        metadata: dict[str, CoreValue] | None = None,
    ) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "health name must str"
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "health name required"
            )

        if not isinstance(
            status,
            HealthStatus,
        ):
            raise TypeError(
                "invalid health status"
            )

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "message must str"
            )

        self._name = name
        self._status = status
        self._message = message
        self._metadata = dict(
            metadata or {}
        )

    @property
    def name(
        self,
    ) -> str:
        return self._name

    @property
    def status(
        self,
    ) -> HealthStatus:
        return self._status

    def ready(
        self,
    ) -> bool:
        return bool(
            self._name
            and isinstance(
                self._status,
                HealthStatus,
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self._name,
            "status": self._status.value,
            "message": self._message,
            "metadata": dict(
                self._metadata
            ),
            "ready": self.ready(),
        }


__all__ = [
    "HealthReport",
]
