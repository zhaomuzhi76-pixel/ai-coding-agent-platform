from __future__ import annotations


class ProjectSessionAPIDiagnosticsMixin:
    """
    Project-session API diagnostics projection.

    Runtime execution is owned by the canonical
    ApplicationRuntimeSubmission boundary.
    """

    runtime_submission: object
    support: object
    adapter: object
    request_count: int

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "request_count": self.request_count,
            "runtime_submission": type(
                self.runtime_submission
            ).__name__
            if self.runtime_submission is not None
            else None,
        }

    def ready(self) -> bool:
        return (
            self.adapter is not None
            and self.adapter.ready()
            and self.support.ready()
            and self.runtime_submission_ready()
        )


__all__ = [
    "ProjectSessionAPIDiagnosticsMixin",
]
