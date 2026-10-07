from __future__ import annotations


class ProcessSupervisionSupport:
    """
    Validation and normalization support for process supervision.
    """

    VERSION = "1.0"

    @staticmethod
    def validate_runner(
        runner: object,
    ):
        if not callable(runner):
            raise TypeError(
                "process runner must be callable"
            )

        return runner

    @staticmethod
    def normalize_exit_code(
        result: object,
    ) -> int:
        if result is None:
            return 0

        if isinstance(
            result,
            bool,
        ):
            return int(result)

        if isinstance(
            result,
            int,
        ):
            return result

        raise TypeError(
            "process runner must return int or None"
        )

    @staticmethod
    def normalize_exception(
        error: BaseException,
    ) -> int:
        if isinstance(
            error,
            SystemExit,
        ):
            return ProcessSupervisionSupport.normalize_exit_code(
                error.code
            )

        return 1

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessSupervisionSupport",
]
