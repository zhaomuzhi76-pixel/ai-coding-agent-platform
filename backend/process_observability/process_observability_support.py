from __future__ import annotations


class ProcessObservabilitySupport:
    """
    Validation support for process observability.

    Owns:
        - structural dependency validation
        - process-state normalization
        - health projection
    """

    VERSION = "1.0"

    REQUIRED_METHODS = (
        "ready",
        "running",
        "failed",
        "exit_code",
        "signal",
        "dump",
    )

    @classmethod
    def validate_control(
        cls,
        control: object,
    ) -> object:
        if control is None:
            raise ValueError(
                "process control required"
            )

        missing = tuple(
            name
            for name in cls.REQUIRED_METHODS
            if not callable(
                getattr(
                    control,
                    name,
                    None,
                )
            )
        )

        if missing:
            raise TypeError(
                "process control missing methods: "
                + ", ".join(missing)
            )

        if not bool(control.ready()):
            raise RuntimeError(
                "process control not ready"
            )

        return control

    @staticmethod
    def project_health(
        control: object,
    ) -> bool:
        if bool(control.failed()):
            return False

        exit_code = control.exit_code()

        if exit_code is None:
            return True

        return exit_code == 0

    @staticmethod
    def project_state(
        control: object,
    ) -> str:
        if bool(control.running()):
            return "running"

        if bool(control.failed()):
            return "failed"

        exit_code = control.exit_code()

        if exit_code is None:
            return "idle"

        if exit_code == 0:
            return "stopped"

        return "failed"

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "required_methods": self.REQUIRED_METHODS,
        }


__all__ = [
    "ProcessObservabilitySupport",
]
