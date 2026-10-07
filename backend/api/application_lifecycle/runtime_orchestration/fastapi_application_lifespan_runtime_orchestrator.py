from __future__ import annotations

from backend.api.application_lifecycle.runtime_orchestration.fastapi_application_lifespan_runtime_orchestrator_contract import (
    FastAPIApplicationLifespanRuntimeOrchestratorContract,
)
from backend.api.application_lifecycle.runtime_orchestration.fastapi_application_lifespan_runtime_orchestrator_support import (
    FastAPIApplicationLifespanRuntimeOrchestratorSupport,
)
from backend.api.application_lifecycle.runtime_orchestration.fastapi_application_lifespan_runtime_phase_coordinator import (
    FastAPIApplicationLifespanRuntimePhaseCoordinator,
)
from backend.api.application_lifecycle.runtime_orchestration.fastapi_application_lifespan_runtime_rollback import (
    FastAPIApplicationLifespanRuntimeRollback,
)


class FastAPIApplicationLifespanRuntimeOrchestrator(
    FastAPIApplicationLifespanRuntimeOrchestratorContract,
):
    """
    Single owner of FastAPI application lifecycle orchestration.

    Startup order:
        WebSocket -> HTTP -> project session -> project registration
        -> code intelligence

    Shutdown order:
        code intelligence -> project registration -> project session
        -> HTTP -> WebSocket
    """

    VERSION = "3.5"

    def __init__(
        self,
        *,
        http_integration: object,
        ws_bootstrap: object,
        project_session_lifecycle: object,
        project_registration_lifecycle: object,
        code_intelligence_lifecycle: object,
        support: (
            FastAPIApplicationLifespanRuntimeOrchestratorSupport
            | None
        ) = None,
    ) -> None:
        self.support = (
            support
            or FastAPIApplicationLifespanRuntimeOrchestratorSupport()
        )
        self.http_integration = (
            self.support.validate_http_integration(
                http_integration
            )
        )
        self.ws_bootstrap = (
            self.support.validate_ws_bootstrap(
                ws_bootstrap
            )
        )
        self.project_session_lifecycle = (
            self.support.validate_project_session_lifecycle(
                project_session_lifecycle
            )
        )
        self.project_registration_lifecycle = (
            self.support.validate_project_registration_lifecycle(
                project_registration_lifecycle
            )
        )
        self.code_intelligence_lifecycle = (
            self.support.validate_api_lifecycle(
                code_intelligence_lifecycle,
                "code intelligence lifecycle",
            )
        )
        self.rollback = FastAPIApplicationLifespanRuntimeRollback(
            http_integration=self.http_integration,
            ws_bootstrap=self.ws_bootstrap,
            project_session_lifecycle=(
                self.project_session_lifecycle
            ),
            project_registration_lifecycle=(
                self.project_registration_lifecycle
            ),
            code_intelligence_lifecycle=(
                self.code_intelligence_lifecycle
            ),
            support=self.support,
        )
        self.phase = FastAPIApplicationLifespanRuntimePhaseCoordinator(
            http_integration=self.http_integration,
            ws_bootstrap=self.ws_bootstrap,
            project_session_lifecycle=(
                self.project_session_lifecycle
            ),
            project_registration_lifecycle=(
                self.project_registration_lifecycle
            ),
            code_intelligence_lifecycle=(
                self.code_intelligence_lifecycle
            ),
            rollback=self.rollback,
            support=self.support,
        )
        self.application = None
        self.started = False
        self.start_count = 0
        self.stop_count = 0

    async def start(
        self,
        *,
        application: object,
        startup: object,
    ) -> None:
        application = self.support.validate_application(
            application
        )
        startup = self.support.validate_startup(
            startup
        )

        if self.started:
            if self.application is application:
                return
            raise RuntimeError(
                "application lifespan orchestrator already bound"
            )

        await self.phase.start(
            application=application,
            startup=startup,
        )
        self.application = application
        self.started = True
        self.start_count += 1

    async def stop(
        self,
        application: object,
    ) -> None:
        application = self.support.validate_application(
            application
        )
        target = self.application or application

        try:
            await self.phase.stop(target)
        finally:
            if self.started:
                self.stop_count += 1
            self.application = None
            self.started = False

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.rollback.ready()
            and self.phase.ready()
            and self.http_integration.ready()
            and self.ws_bootstrap.ready()
            and self.project_session_lifecycle.ready()
            and self.project_registration_lifecycle.ready()
            and self.code_intelligence_lifecycle.ready()
            and (
                not self.started
                or all(
                    (
                        self.http_integration.registered(),
                        self.project_session_lifecycle.registered(),
                        self.project_registration_lifecycle.registered(),
                        self.code_intelligence_lifecycle.registered(),
                    )
                )
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self.started,
            "start_count": self.start_count,
            "stop_count": self.stop_count,
            "http_integration": self.http_integration.dump(),
            "ws_bootstrap": self.ws_bootstrap.dump(),
            "project_session_lifecycle": (
                self.project_session_lifecycle.dump()
            ),
            "project_registration_lifecycle": (
                self.project_registration_lifecycle.dump()
            ),
            "code_intelligence_lifecycle": (
                self.code_intelligence_lifecycle.dump()
            ),
            "phase": self.phase.dump(),
            "rollback": self.rollback.dump(),
        }


__all__ = [
    "FastAPIApplicationLifespanRuntimeOrchestrator",
]
