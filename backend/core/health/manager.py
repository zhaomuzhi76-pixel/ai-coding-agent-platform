from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.health.check import HealthCheckProtocol
from backend.core.health.status import HealthStatus


class HealthManager:
    """
    Canonical health check registry and aggregator.
    """

    VERSION = "2.0"

    def __init__(self) -> None:
        self._checks: dict[
            str,
            HealthCheckProtocol,
        ] = {}

    def register(
        self,
        name: str,
        check: HealthCheckProtocol,
    ) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "health check name must str"
            )

        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError(
                "health check name required"
            )

        if check is None:
            raise ValueError(
                "health check required"
            )

        if not isinstance(
            check,
            HealthCheckProtocol,
        ):
            raise TypeError(
                "health check contract required"
            )

        if normalized_name in self._checks:
            raise ValueError(
                f"health check exists: {normalized_name}"
            )

        self._checks[normalized_name] = check

    def check(self) -> dict[str, HealthStatus]:
        return {
            name: checker.check()
            for name, checker in self._checks.items()
        }

    def status(self) -> HealthStatus:
        results = list(self.check().values())

        if not results:
            return HealthStatus.UNKNOWN

        if all(
            item is HealthStatus.HEALTHY
            for item in results
        ):
            return HealthStatus.HEALTHY

        if any(
            item is HealthStatus.UNHEALTHY
            for item in results
        ):
            return HealthStatus.UNHEALTHY

        return HealthStatus.DEGRADED

    def ready(self) -> bool:
        return all(
            isinstance(
                checker,
                HealthCheckProtocol,
            )
            for checker in self._checks.values()
        )

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "checks": tuple(self._checks),
            "status": self.status().value,
            "ready": self.ready(),
        }


__all__ = [
    "HealthManager",
]
