from __future__ import annotations


class ProcessRuntimeEntrySupport:
    """
    Validation support for the process runtime entry.
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
    def validate_supervision(
        cls,
        supervision: object,
    ) -> object:
        if supervision is None:
            raise ValueError(
                "process supervision required"
            )

        missing = [
            name
            for name in cls.REQUIRED_METHODS
            if not callable(
                getattr(
                    supervision,
                    name,
                    None,
                )
            )
        ]

        if missing:
            raise TypeError(
                "invalid process supervision: "
                + ", ".join(missing)
            )

        if not supervision.ready():
            raise RuntimeError(
                "process supervision not ready"
            )

        return supervision

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessRuntimeEntrySupport",
]
