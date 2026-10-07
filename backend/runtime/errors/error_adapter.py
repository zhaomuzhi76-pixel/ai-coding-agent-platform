from __future__ import annotations

from backend.core.errors import (
    CoreErrorCode,
    CoreErrorDetail,
)


class RuntimeErrorAdapter:
    """
    Canonical Runtime-to-Core error adapter.

    Ownership:
        - classify runtime exceptions
        - normalize them into CoreErrorDetail

    Not Responsible:
        - exception ownership
        - runtime execution
        - transport response formatting
        - application business rules
    """

    VERSION = "1.0"

    TYPE_MAPPING = {
        ValueError: CoreErrorCode.VALIDATION,
        TypeError: CoreErrorCode.VALIDATION,
        LookupError: CoreErrorCode.NOT_FOUND,
        TimeoutError: CoreErrorCode.TIMEOUT,
        RuntimeError: CoreErrorCode.EXECUTION,
    }

    def adapt(
        self,
        error: BaseException,
        *,
        operation: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CoreErrorDetail:
        if error is None:
            raise ValueError(
                "runtime error required"
            )

        if not isinstance(
            error,
            BaseException,
        ):
            raise TypeError(
                "runtime error must BaseException"
            )

        code = self._code(error)

        details = dict(
            metadata or {}
        )

        details.setdefault(
            "exception_type",
            type(error).__name__,
        )

        if operation:
            details.setdefault(
                "operation",
                operation,
            )

        return CoreErrorDetail(
            code=code,
            message=self._message(error),
            metadata=details,
        )

    def ready(self) -> bool:
        return bool(self.TYPE_MAPPING)

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "mapping_count": len(
                self.TYPE_MAPPING
            ),
            "ready": self.ready(),
        }

    def _code(
        self,
        error: BaseException,
    ) -> CoreErrorCode:
        for error_type, code in self.TYPE_MAPPING.items():
            if isinstance(error, error_type):
                return code

        return CoreErrorCode.INTERNAL

    def _message(
        self,
        error: BaseException,
    ) -> str:
        message = str(error).strip()

        if message:
            return message

        return type(error).__name__


__all__ = [
    "RuntimeErrorAdapter",
]
