from __future__ import annotations


class ProcessHealthSupport:
    """
    Validation support for the process health boundary.

    Owns only:
        - observability dependency validation
        - snapshot normalization
        - health-state projection
    """

    VERSION = "1.0"

    REQUIRED_METHODS = (
        "snapshot",
        "healthy",
        "failed",
        "ready",
        "dump",
    )

    @classmethod
    def validate_observability(
        cls,
        observability: object,
    ) -> object:
        if observability is None:
            raise ValueError(
                "process observability required"
            )

        missing = tuple(
            name
            for name in cls.REQUIRED_METHODS
            if not callable(
                getattr(
                    observability,
                    name,
                    None,
                )
            )
        )

        if missing:
            raise TypeError(
                "process observability missing methods: "
                + ", ".join(missing)
            )

        if not bool(
            observability.ready()
        ):
            raise RuntimeError(
                "process observability not ready"
            )

        return observability

    @staticmethod
    def normalize_snapshot(
        snapshot: object,
    ) -> dict[str, object]:
        if not isinstance(
            snapshot,
            dict,
        ):
            raise TypeError(
                "process observability snapshot must dict"
            )

        return dict(snapshot)

    @staticmethod
    def project_status(
        snapshot: dict[str, object],
    ) -> str:
        if bool(
            snapshot.get("failed", False)
        ):
            return "failed"

        if bool(
            snapshot.get("running", False)
        ):
            return "running"

        if bool(
            snapshot.get("healthy", False)
        ):
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
    "ProcessHealthSupport",
]
