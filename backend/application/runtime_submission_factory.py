from __future__ import annotations

from backend.application.runtime_execution_gateway import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.application.runtime_submission import (
    ApplicationRuntimeSubmission,
)


class ApplicationRuntimeSubmissionFactory:
    """
    Canonical runtime submission factory.

    Owns:
        - construction of ApplicationRuntimeSubmission

    Does not own:
        - runtime execution construction
        - capability registration
        - submission lifecycle
        - transport
    """

    VERSION = "2.0"

    def create(
        self,
        execution_gateway: ApplicationRuntimeExecutionGatewayContract,
    ) -> ApplicationRuntimeSubmission:
        if not isinstance(
            execution_gateway,
            ApplicationRuntimeExecutionGatewayContract,
        ):
            raise TypeError(
                "execution_gateway must implement "
                "ApplicationRuntimeExecutionGatewayContract"
            )

        if not execution_gateway.ready():
            raise RuntimeError(
                "runtime execution gateway not ready"
            )

        submission = ApplicationRuntimeSubmission(
            execution_gateway=execution_gateway,
        )

        if not submission.ready():
            raise RuntimeError(
                "runtime submission unavailable"
            )

        return submission

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
    "ApplicationRuntimeSubmissionFactory",
]
