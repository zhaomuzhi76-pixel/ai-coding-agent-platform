from __future__ import annotations


class ProcessOperationsSupport:
    """
    Validation and projection support for process operations.

    Owns only:
        - lower-layer dependency validation
        - status normalization
        - aggregate state projection
    """

    VERSION = "1.0"

    REQUIRED_CONTROL_METHODS = (
        "running",
        "failed",
        "exit_code",
        "signal",
        "ready",
        "dump",
    )

    REQUIRED_HEALTH_METHODS = (
        "healthy",
        "failed",
        "ready",
        "status",
        "snapshot",
        "dump",
    )

    @classmethod
    def validate_control(
        cls,
        control: object,
    ) -> object:
        return cls._validate(
            control,
            cls.REQUIRED_CONTROL_METHODS,
            "process control",
        )

    @classmethod
    def validate_health(
        cls,
        health: object,
    ) -> object:
        return cls._validate(
            health,
            cls.REQUIRED_HEALTH_METHODS,
            "process health",
        )

    @classmethod
    def validate_observability(
        cls,
        observability: object,
    ) -> object:
        required = (
            "healthy",
            "failed",
            "ready",
            "snapshot",
            "dump",
        )

        return cls._validate(
            observability,
            required,
            "process observability",
        )

    @staticmethod
    def _validate(
        dependency: object,
        methods: tuple[str, ...],
        label: str,
    ) -> object:
        if dependency is None:
            raise ValueError(
                f"{label} required"
            )

        missing = tuple(
            name
            for name in methods
            if not callable(
                getattr(
                    dependency,
                    name,
                    None,
                )
            )
        )

        if missing:
            raise TypeError(
                f"{label} missing required methods: "
                + ", ".join(missing)
            )

        if not bool(
            dependency.ready()
        ):
            raise RuntimeError(
                f"{label} not ready"
            )

        return dependency

    @staticmethod
    def project_status(
        *,
        running: bool,
        failed: bool,
        healthy: bool,
    ) -> str:
        if failed:
            return "failed"

        if running:
            return "running"

        if healthy:
            return "healthy"

        return "unhealthy"

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessOperationsSupport",
]
