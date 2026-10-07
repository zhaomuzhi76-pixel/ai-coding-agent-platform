from __future__ import annotations

from backend.runtime.errors.consumer_composition import (
    RuntimeErrorConsumerComposition,
)
from backend.runtime.errors.consumer_contract import (
    RuntimeErrorConsumerProtocol,
)
from backend.runtime.errors.domains.domain import (
    RuntimeErrorDomain,
)
from backend.runtime.errors.domains.domain_binding import (
    RuntimeErrorDomainBinding,
)
from backend.runtime.errors.domains.domain_contract import (
    RuntimeErrorDomainBindingProtocol,
)


class RuntimeErrorDomainComposition:
    """
    Runtime error domain binding composition boundary.

    Responsibility:
        - create all canonical runtime error domain bindings
        - share one canonical RuntimeErrorConsumer
        - expose domain lookup

    Not Responsible:
        - exception classification
        - normalization
        - runtime execution
        - transport formatting
        - application policy
    """

    VERSION = "1.0"

    def __init__(
        self,
        consumer: RuntimeErrorConsumerProtocol | None = None,
    ) -> None:
        self.consumer = (
            consumer
            if consumer is not None
            else RuntimeErrorConsumerComposition().create()
        )

        if not isinstance(
            self.consumer,
            RuntimeErrorConsumerProtocol,
        ):
            raise TypeError(
                "runtime error consumer contract required"
            )

        self._bindings = {
            domain.value: RuntimeErrorDomainBinding(
                domain,
                self.consumer,
            )
            for domain in RuntimeErrorDomain
        }

    def create(
        self,
    ) -> dict[
        str,
        RuntimeErrorDomainBindingProtocol,
    ]:
        if not self.ready():
            raise RuntimeError(
                "runtime error domain composition unavailable"
            )

        return dict(
            self._bindings
        )

    def resolve(
        self,
        domain: RuntimeErrorDomain | str,
    ) -> RuntimeErrorDomainBindingProtocol:
        key = (
            domain.value
            if isinstance(domain, RuntimeErrorDomain)
            else domain
        )

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "runtime error domain must str"
            )

        binding = self._bindings.get(
            key.strip()
        )

        if binding is None:
            raise LookupError(
                f"runtime error domain not found: {key}"
            )

        return binding

    def ready(
        self,
    ) -> bool:
        return (
            RuntimeErrorDomain.ready()
            and self.consumer.ready()
            and all(
                binding.ready()
                for binding in self._bindings.values()
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "domain_count": len(
                self._bindings
            ),
            "domains": tuple(
                self._bindings.keys()
            ),
            "ready": self.ready(),
            "consumer": self.consumer.dump(),
        }


__all__ = [
    "RuntimeErrorDomainComposition",
]
