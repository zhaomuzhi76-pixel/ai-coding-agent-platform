from __future__ import annotations

from backend.core.errors import CoreErrorDetail
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)
from backend.runtime.errors.domains.domain import (
    RuntimeErrorDomain,
)
from backend.runtime.errors.domains.domain_contract import (
    RuntimeErrorDomainBindingProtocol,
)


class RuntimeErrorDomainBinding(
    RuntimeErrorDomainBindingProtocol,
):
    """
    Stable runtime error ownership binding.

    Responsibility:
        - bind one runtime domain to the canonical consumer
        - preserve domain identity during consumption

    Not Responsible:
        - normalization
        - exception classification
        - runtime execution
        - transport formatting
        - application policy
    """

    VERSION = "1.0"

    def __init__(
        self,
        domain: RuntimeErrorDomain | str,
        consumer: RuntimeErrorConsumerProtocol,
    ) -> None:
        normalized_domain = self._normalize_domain(
            domain
        )

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

        self._domain = normalized_domain
        self.consumer = consumer
        self.consume_count = 0

    @property
    def domain(
        self,
    ) -> str:
        return self._domain.value

    def consume(
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

        if not self.ready():
            raise RuntimeError(
                "runtime error consumer unavailable"
            )

        result = self.consumer.consume(
            error,
            domain=self.domain,
            operation=operation,
            metadata=metadata,
        )

        self.consume_count += 1
        return result

    def ready(
        self,
    ) -> bool:
        return (
            RuntimeErrorDomain.ready()
            and self.consumer.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "domain": self.domain,
            "consume_count": self.consume_count,
            "ready": self.ready(),
            "consumer": self.consumer.dump(),
        }

    @staticmethod
    def _normalize_domain(
        domain: RuntimeErrorDomain | str,
    ) -> RuntimeErrorDomain:
        if isinstance(
            domain,
            RuntimeErrorDomain,
        ):
            return domain

        if not isinstance(
            domain,
            str,
        ):
            raise TypeError(
                "runtime error domain must str"
            )

        value = domain.strip()

        try:
            return RuntimeErrorDomain(
                value
            )
        except ValueError as error:
            raise ValueError(
                f"unsupported runtime error domain: {value}"
            ) from error


__all__ = [
    "RuntimeErrorDomainBinding",
]
