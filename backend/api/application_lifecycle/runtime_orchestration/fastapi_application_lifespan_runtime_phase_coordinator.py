from __future__ import annotations
from backend.api.server.ws_tree_bootstrap import (
    WSTreeBootstrap,
)

import inspect


class FastAPIApplicationLifespanRuntimePhaseCoordinator:
    """
    Coordinates the ordered startup/shutdown phases of the application
    runtime surface.

    Owns only:
        - startup ordering
        - shutdown ordering
        - failed-start rollback

    Does not own:
        - application construction
        - dependency construction
        - lifecycle state ownership
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
        rollback: object,
        support: object,
    ) -> None:
        self.http_integration = http_integration
        self.ws_bootstrap = ws_bootstrap
        self.project_session_lifecycle = project_session_lifecycle
        self.project_registration_lifecycle = (
            project_registration_lifecycle
        )
        self.code_intelligence_lifecycle = (
            code_intelligence_lifecycle
        )
        self.rollback = rollback
        self.support = support

    async def start(
        self,
        *,
        application: object,
        startup: object,
    ) -> None:
        ws_started = False
        http_started = False
        session_attempted = False
        registration_attempted = False
        code_intelligence_attempted = False

        try:
            self.ws_bootstrap.build(
                startup,
                application,
            )

            # /ws/tree 路由（幂等；与 /ws/agent 独立通道）
            WSTreeBootstrap().build(application)

            ws_started = True

            result = self.http_integration.start(
                application=application,
                startup=startup,
            )
            await self._await_if_needed(result)
            self._require_registered(
                self.http_integration,
                "http runtime integration",
            )
            http_started = True

            session_attempted = True
            self.project_session_lifecycle.register(
                application,
                startup,
            )
            self._require_registered(
                self.project_session_lifecycle,
                "project session api",
            )

            registration_attempted = True
            self.project_registration_lifecycle.register(
                application,
                startup,
            )
            self._require_registered(
                self.project_registration_lifecycle,
                "project registration api",
            )

            code_intelligence_attempted = True
            self.code_intelligence_lifecycle.register(
                application,
                startup,
            )
            self._require_registered(
                self.code_intelligence_lifecycle,
                "code intelligence api",
            )
        except Exception:
            await self.rollback.rollback(
                application,
                http_started=http_started,
                project_session_attempted=session_attempted,
                project_registration_attempted=registration_attempted,
                code_intelligence_attempted=(
                    code_intelligence_attempted
                ),
                ws_started=ws_started,
            )
            raise

    async def stop(
        self,
        application: object,
    ) -> None:
        try:
            self.code_intelligence_lifecycle.unregister(
                application
            )
            self.project_registration_lifecycle.unregister(
                application
            )
            self.project_session_lifecycle.unregister(
                application
            )
        finally:
            try:
                result = self.http_integration.stop(
                    application
                )
                await self._await_if_needed(result)
            finally:
                result = self.ws_bootstrap.stop(
                    application
                )
                await self._await_if_needed(result)

    def ready(self) -> bool:
        return all(
            dependency is not None
            for dependency in (
                self.http_integration,
                self.ws_bootstrap,
                self.project_session_lifecycle,
                self.project_registration_lifecycle,
                self.code_intelligence_lifecycle,
                self.rollback,
                self.support,
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _require_registered(
        dependency: object,
        label: str,
    ) -> None:
        if not dependency.registered():
            raise RuntimeError(
                f"{label} unavailable"
            )

    @staticmethod
    async def _await_if_needed(
        result: object,
    ) -> None:
        if inspect.isawaitable(result):
            await result


__all__ = [
    "FastAPIApplicationLifespanRuntimePhaseCoordinator",
]
