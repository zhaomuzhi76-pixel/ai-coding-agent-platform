from __future__ import annotations


class FastAPIApplicationLifespanRuntimeRollback:
    """
    Lifecycle rollback boundary.

    Owns only failed-start rollback.
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        http_integration: object,
        ws_bootstrap: object,
        project_session_lifecycle: object,
        project_registration_lifecycle: object,
        code_intelligence_lifecycle: object,
        support,
    ) -> None:
        self.http_integration = http_integration
        self.ws_bootstrap = ws_bootstrap
        self.project_session_lifecycle = (
            project_session_lifecycle
        )
        self.project_registration_lifecycle = (
            project_registration_lifecycle
        )
        self.code_intelligence_lifecycle = (
            code_intelligence_lifecycle
        )
        self.support = support

    async def rollback(
        self,
        application: object,
        *,
        http_started: bool,
        project_session_attempted: bool,
        project_registration_attempted: bool,
        code_intelligence_attempted: bool,
        ws_started: bool,
    ) -> None:
        if code_intelligence_attempted:
            self.code_intelligence_lifecycle.unregister(
                application
            )

        if project_registration_attempted:
            self.project_registration_lifecycle.unregister(
                application
            )

        if project_session_attempted:
            self.project_session_lifecycle.unregister(
                application
            )

        if http_started:
            result = self.http_integration.stop(
                application
            )
            await self.support.await_if_needed(result)

        if ws_started:
            result = self.ws_bootstrap.stop(
                application
            )
            await self.support.await_if_needed(result)

    def ready(self) -> bool:
        return all(
            dependency is not None
            for dependency in (
                self.http_integration,
                self.ws_bootstrap,
                self.project_session_lifecycle,
                self.project_registration_lifecycle,
                self.code_intelligence_lifecycle,
                self.support,
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "FastAPIApplicationLifespanRuntimeRollback",
]
