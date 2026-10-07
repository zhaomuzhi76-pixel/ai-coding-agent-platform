from __future__ import annotations

import signal


class ProcessControlSupport:
    """
    Validation and normalization support for process control.
    """

    VERSION = "1.0"

    @staticmethod
    def validate_runner(
        runner: object,
    ):
        if not callable(runner):
            raise TypeError(
                "process control runner must be callable"
            )

        return runner

    @staticmethod
    def normalize_result(
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
            "process control runner must return int or None"
        )

    @staticmethod
    def normalize_exception(
        error: BaseException,
    ) -> int:
        if isinstance(
            error,
            SystemExit,
        ):
            return ProcessControlSupport.normalize_result(
                error.code
            )

        if isinstance(
            error,
            KeyboardInterrupt,
        ):
            return 130

        return 1

    @staticmethod
    def normalize_signal(
        signum: int,
    ) -> int:
        if not isinstance(
            signum,
            int,
        ):
            raise TypeError(
                "signal number must be int"
            )

        return signum

    @staticmethod
    def signal_name(
        signum: int | None,
    ) -> str | None:
        if signum is None:
            return None

        try:
            return signal.Signals(
                signum
            ).name
        except ValueError:
            return str(signum)

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessControlSupport",
]
