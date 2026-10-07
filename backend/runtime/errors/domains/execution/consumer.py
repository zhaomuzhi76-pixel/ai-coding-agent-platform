from __future__ import annotations

from backend.core.errors import CoreErrorDetail
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)
from backend.runtime.errors.domains.domain import (
    RuntimeErrorDomain,
)


class RuntimeExecutionErrorConsumer:
    """
    Execution-domain error consumption facade.

    Responsibility:
        - bind Execution domain identity
        - delegate failure consumption to shared runtime consumer
        - preserve canonical CoreErrorDetail

    Not Responsible:
        - exception classification
        - normalization implementation
        - execution orchestration
        - transport formatting
        - logging
    """

    VERSION = "1.0"
    DOMAIN = RuntimeErrorDomain.EXECUTION

    def __init__(
        self,
        consumer: RuntimeErrorConsumerProtocol,
    ) -> None:
        if consumer is None:
            raise ValueError(
                "runtime error consumer required"
            )

        if not isinstance(
            consumer,
            RuntimeErrorConsumerProtocol,
        ):
            raise TypeError(
                "runtime error consumer contract required"
            )

        self.consumer = consumer
        self.consume_count = 0
        self.last_error: CoreErrorDetail | None = None

    def consume(
        self,
        error: BaseException,
        *,
        operation: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CoreErrorDetail:
        self._validate(
            error,
            metadata,
        )

        details = dict(
            metadata or {}
        )

        details.setdefault(
            "domain",
            self.DOMAIN.value,
        )

        result = self.consumer.consume(
            error,
            domain=self.DOMAIN.value,
            operation=operation,
            metadata=details,
        )

        self.consume_count += 1
        self.last_error = result

        return result

    def ready(
        self,
    ) -> bool:
        return self.consumer.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "domain": self.DOMAIN.value,
            "ready": self.ready(),
            "consume_count": self.consume_count,
            "last_error": (
                self.last_error.dump()
                if self.last_error is not None
                else None
            ),
        }

    @staticmethod
    def _validate(
        error: BaseException,
        metadata: dict[str, object] | None,
    ) -> None:
        if error is None:
            raise ValueError(
                "execution runtime error required"
            )

        if not isinstance(
            error,
            BaseException,
        ):
            raise TypeError(
                "execution runtime error must BaseException"
            )

        if metadata is not None and not isinstance(
            metadata,
            dict,
        ):
            raise TypeError(
                "execution metadata must dict or None"
            )


__all__ = [
    "RuntimeExecutionErrorConsumer",
]
