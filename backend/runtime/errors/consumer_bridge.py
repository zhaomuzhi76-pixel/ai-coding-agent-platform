from __future__ import annotations

from backend.core.errors import CoreErrorDetail
from backend.runtime.errors.normalization_contract import (
    RuntimeErrorNormalizationProtocol,
)
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)


class RuntimeErrorConsumerBridge(
    RuntimeErrorConsumerProtocol,
):
    """
    Canonical Runtime error consumption bridge.

    Ownership:
        - provide the stable consumption boundary for Runtime domains
        - preserve domain identity
        - delegate normalization downward

    Not Responsible:
        - exception classification
        - runtime execution
        - transport formatting
        - application policy
        - logging
    """

    VERSION = "1.0"

    def __init__(
        self,
        normalizer: RuntimeErrorNormalizationProtocol,
    ) -> None:
        if normalizer is None:
            raise ValueError(
                "runtime error normalizer required"
            )

        if not isinstance(
            normalizer,
            RuntimeErrorNormalizationProtocol,
        ):
            raise TypeError(
                "runtime error normalization contract required"
            )

        self.normalizer = normalizer
        self.consume_count = 0
        self.last_domain: str | None = None
        self.last_error: CoreErrorDetail | None = None

    def consume(
        self,
        error: BaseException,
        *,
        domain: str,
        operation: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CoreErrorDetail:
        self._validate(
            error,
            domain,
            metadata,
        )

        details = dict(
            metadata or {}
        )
        details.setdefault(
            "domain",
            domain.strip(),
        )

        normalized = self.normalizer.normalize(
            error,
            operation=operation,
            metadata=details,
        )

        self.consume_count += 1
        self.last_domain = domain.strip()
        self.last_error = normalized

        return normalized

    def ready(
        self,
    ) -> bool:
        return self.normalizer.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "consume_count": self.consume_count,
            "last_domain": self.last_domain,
            "last_error": (
                self.last_error.dump()
                if self.last_error is not None
                else None
            ),
            "normalizer": self.normalizer.dump(),
        }

    @staticmethod
    def _validate(
        error: BaseException,
        domain: str,
        metadata: dict[str, object] | None,
    ) -> None:
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

        if not isinstance(
            domain,
            str,
        ) or not domain.strip():
            raise ValueError(
                "runtime error domain required"
            )

        if metadata is not None and not isinstance(
            metadata,
            dict,
        ):
            raise TypeError(
                "metadata must dict or None"
            )


__all__ = [
    "RuntimeErrorConsumerBridge",
]
