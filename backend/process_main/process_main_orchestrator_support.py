from __future__ import annotations


class ProcessMainOrchestratorSupport:
    """
    Structural validation support for process main orchestration.
    """

    VERSION = "1.0"

    REQUIRED_METHODS = (
        "run",
        "ready",
        "running",
        "failed",
        "dump",
    )

    @classmethod
    def validate_runtime_entry(
        cls,
        entry: object,
    ) -> object:
        if entry is None:
            raise ValueError(
                "process runtime entry required"
            )

        missing = [
            name
            for name in cls.REQUIRED_METHODS
            if not callable(
                getattr(
                    entry,
                    name,
                    None,
                )
            )
        ]

        if missing:
            raise TypeError(
                "invalid process runtime entry: "
                + ", ".join(missing)
            )

        if not entry.ready():
            raise RuntimeError(
                "process runtime entry not ready"
            )

        return entry

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessMainOrchestratorSupport",
]
