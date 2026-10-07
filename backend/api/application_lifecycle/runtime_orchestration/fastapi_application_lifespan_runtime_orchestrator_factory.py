from __future__ import annotations

from backend.api.application_lifecycle.application_http_integration import (
    FastAPIApplicationLifespanHTTPRuntimeIntegrationFactory,
)
from backend.api.application_lifecycle.runtime_orchestration.fastapi_application_lifespan_runtime_orchestrator import (
    FastAPIApplicationLifespanRuntimeOrchestrator,
)
from backend.api.application_lifecycle.runtime_orchestration.fastapi_application_lifespan_runtime_orchestrator_support import (
    FastAPIApplicationLifespanRuntimeOrchestratorSupport,
)
from backend.api.code_intelligence import (
    CodeIntelligenceServerLifecycle,
)
from backend.api.server.project_registration_server_lifecycle import (
    ProjectRegistrationServerLifecycle,
)
from backend.api.server.project_session_server_lifecycle import (
    ProjectSessionServerLifecycle,
)
from backend.api.server.ws_agent_bootstrap import (
    WSAgentBootstrap,
)


class FastAPIApplicationLifespanRuntimeOrchestratorFactory:
    """
    Construction boundary for the canonical lifespan orchestrator.
    """

    VERSION = "1.2"

    def create(
        self,
        *,
        http_integration=None,
        ws_bootstrap=None,
        project_session_lifecycle=None,
        project_registration_lifecycle=None,
        code_intelligence_lifecycle=None,
        support=None,
    ) -> FastAPIApplicationLifespanRuntimeOrchestrator:
        active_http = (
            http_integration
            or FastAPIApplicationLifespanHTTPRuntimeIntegrationFactory()
            .create()
        )
        active_ws = (
            ws_bootstrap
            or WSAgentBootstrap()
        )
        active_project_session = (
            project_session_lifecycle
            or ProjectSessionServerLifecycle()
        )
        active_project_registration = (
            project_registration_lifecycle
            or ProjectRegistrationServerLifecycle()
        )
        active_code_intelligence = (
            code_intelligence_lifecycle
            or CodeIntelligenceServerLifecycle()
        )
        active_support = (
            support
            or FastAPIApplicationLifespanRuntimeOrchestratorSupport()
        )

        return FastAPIApplicationLifespanRuntimeOrchestrator(
            http_integration=active_http,
            ws_bootstrap=active_ws,
            project_session_lifecycle=active_project_session,
            project_registration_lifecycle=(
                active_project_registration
            ),
            code_intelligence_lifecycle=(
                active_code_intelligence
            ),
            support=active_support,
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "FastAPIApplicationLifespanRuntimeOrchestratorFactory",
]
