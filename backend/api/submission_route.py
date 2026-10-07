from __future__ import annotations

from backend.api.submission_binding import (
    APISubmissionBinding,
)
from backend.api.submission_route_contract import (
    APISubmissionRouteProtocol,
)
from backend.api.ws_agent_request import (
    WSAgentRequestBuilder,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)
from backend.core.result import ExecutionResult


class APISubmissionRoute(APISubmissionRouteProtocol):
    """
    Canonical transport-neutral submission route.

    Owns:
        - request translation
        - session validation
        - delegation to ApplicationRuntimeSubmission

    Does not own:
        - runtime gateway
        - capability construction
        - execution construction
        - queue
        - scheduler
        - dispatch
        - retry
        - budget
        - rate limiting
        - result creation
        - transport serialization
    """

    VERSION = "3.0"

    def __init__(
        self,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
        request_builder: WSAgentRequestBuilder | None = None,
    ) -> None:
        if runtime_submission is None:
            raise ValueError(
                "application runtime submission required"
            )

        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime_submission must implement "
                "ApplicationRuntimeSubmissionProtocol"
            )

        self.binding = APISubmissionBinding(
            runtime_submission
        )
        self.request_builder = (
            request_builder
            or WSAgentRequestBuilder()
        )
        self.execution_count = 0
        self.failure_count = 0

    async def execute(
        self,
        payload: dict[str, object],
        session_id: str,
    ) -> ExecutionResult:
        self._validate_transport(
            payload=payload,
            session_id=session_id,
        )

        request = self.request_builder.build(
            payload,
            session_id,
        )

        try:
            result = await self.binding.execute(
                request=request,
                session_id=session_id,
            )

            if not isinstance(
                result,
                ExecutionResult,
            ):
                raise TypeError(
                    "submission route must return ExecutionResult"
                )

            self.execution_count += 1
            return result

        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return (
            self.binding.ready()
            and self.request_builder.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "runtime_submission": type(
                self.binding.runtime_submission
            ).__name__,
            "binding": self.binding.dump(),
            "request_builder": (
                self.request_builder.dump()
            ),
        }

    @staticmethod
    def _validate_transport(
        *,
        payload: dict[str, object],
        session_id: str,
    ) -> None:
        if not isinstance(
            payload,
            dict,
        ):
            raise TypeError(
                "submission payload must be dict"
            )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )


__all__ = [
    "APISubmissionRoute",
]
