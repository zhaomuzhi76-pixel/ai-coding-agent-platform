from __future__ import annotations


class ProjectSessionAPIServerRegistrationDiagnosticsMixin:
    """
    Registration diagnostics and construction readiness.

    Construction readiness means the registration boundary has
    valid factories/support available. Runtime route objects are
    intentionally absent until register() executes.
    """

    api: object
    router: object
    runtime_submission: object
    support: object
    adapter_factory: object
    api_factory: object
    _registered_routes: tuple[object, ...]

    def ready(self) -> bool:
        return (
            self.adapter_factory is not None
            and self.adapter_factory.ready()
            and self.api_factory is not None
            and self.api_factory.ready()
            and self.support is not None
            and self.support.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "api": (
                type(self.api).__name__
                if self.api is not None
                else None
            ),
            "router": (
                type(self.router).__name__
                if self.router is not None
                else None
            ),
            "runtime_submission": (
                type(
                    self.runtime_submission
                ).__name__
                if self.runtime_submission is not None
                else None
            ),
            "registered_route_count": len(
                self._registered_routes
            ),
        }


__all__ = [
    "ProjectSessionAPIServerRegistrationDiagnosticsMixin",
]
