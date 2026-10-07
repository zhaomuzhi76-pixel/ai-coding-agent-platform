from __future__ import annotations

from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class SubmissionRouterLifecycleSupport:
    """Validation and runtime-submission resolution support."""

    VERSION = "1.0"

    @classmethod
    def validate_startup(cls, startup: object) -> None:
        if startup is None:
            raise ValueError("startup required")

        runtime_submission = getattr(
            startup,
            "runtime_submission",
            None,
        )
        if runtime_submission is None:
            raise RuntimeError(
                "application runtime submission unavailable"
            )
        if not runtime_submission.ready():
            raise RuntimeError(
                "runtime submission unavailable"
            )

        if getattr(startup, "runtime", None) is None:
            raise RuntimeError(
                "runtime component provider unavailable"
            )

        binding = getattr(
            startup,
            "project_session_binding",
            None,
        )
        if binding is None or not binding.ready():
            raise RuntimeError(
                "project session startup binding unavailable"
            )

        integration = getattr(
            binding,
            "integration",
            None,
        )
        if integration is None or not integration.ready():
            raise RuntimeError(
                "project session integration unavailable"
            )

    @classmethod
    def resolve_runtime_submission(
        cls,
        startup: object,
    ) -> ApplicationRuntimeSubmissionProtocol:
        binding = getattr(
            startup,
            "project_session_binding",
            None,
        )
        if binding is None:
            raise RuntimeError(
                "project session startup binding unavailable"
            )

        integration = getattr(
            binding,
            "integration",
            None,
        )
        if integration is None:
            raise RuntimeError(
                "project session integration unavailable"
            )

        resolver = getattr(
            integration,
            "runtime_submission",
            None,
        )
        if not callable(resolver):
            raise TypeError(
                "project session integration must expose "
                "runtime_submission()"
            )

        runtime_submission = resolver()

        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "project session runtime submission must "
                "implement ApplicationRuntimeSubmissionProtocol"
            )

        if not runtime_submission.ready():
            raise RuntimeError(
                "project session runtime submission unavailable"
            )

        return runtime_submission

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SubmissionRouterLifecycleSupport",
]
