from __future__ import annotations

from backend.application.composition.runtime_port_adapter import ApplicationRuntimePortAdapter
from typing import Any

from backend.application.code_modification_proposal_startup_binding import (
    CodeModificationProposalStartupBinding,
)
from backend.application.composition.capability import (
    ApplicationCapabilityComposition,
)
from backend.application.modules.registry import (
    ApplicationModuleRegistry,
)
from backend.application.operational.project_session.startup import (
    ProjectSessionStartupBinding,
)
from backend.application.planning.startup_binding import (
    PlanningStartupBinding,
)
from backend.application.project.project_removal_factory import (
    ApplicationProjectRemovalFactory,
)
from backend.application.project_session.project_session_adapter_factory import (
    ProjectSessionApplicationAdapterFactory,
)
from backend.application.runtime_submission_factory import (
    ApplicationRuntimeSubmissionFactory,
)
from backend.application.startup_application_execution_assembly import (
    ApplicationStartupExecutionAssembly,
)
from backend.application.startup_assembly_support import (
    ApplicationStartupAssemblySupport,
)
from backend.application.startup_project_session_projection import (
    ApplicationStartupProjectSessionProjection,
)
from backend.application.startup_support import (
    ApplicationStartupSupport,
)
from backend.application.tool.startup_binding import (
    ToolApplicationStartupBinding,
)
from backend.core.planning import PlannerPortProtocol


class ApplicationStartupAssemblyBuilder:
    """
    Application startup orchestration boundary.

    Owns:
        - startup ordering
        - project-session assembly
        - production wiring projection
        - execution capability binding order

    Does not own execution dependency construction.
    """

    VERSION = "5.2"

    def __init__(
        self,
        support: ApplicationStartupAssemblySupport,
    ) -> None:
        self.support = support
        self.execution = ApplicationStartupExecutionAssembly()

    def build(
        self,
        *,
        registry: ApplicationModuleRegistry,
        capability_composition: ApplicationCapabilityComposition,
        planning_binding: PlanningStartupBinding,
        code_intelligence_binding: Any,
        tool_binding: ToolApplicationStartupBinding,
        project_session_composition: Any,
        project_session_operational: Any,
        project_session_binding: ProjectSessionStartupBinding,
        project_registry: object,
        project_registration: object,
        planner: PlannerPortProtocol,
    ) -> dict[str, Any]:
        manager = capability_composition.create()
        ApplicationStartupSupport.validate_manager(manager)

        context = dict(registry.build())
        self.support.validate_context(context)

        ApplicationStartupProjectSessionProjection().project(
            composition=project_session_composition,
            project_registry=project_registry,
            context=context,
        )

        service = context["project_session_service"]
        construction = self.support.require_runtime(context)

        proposal_capability = (
            CodeModificationProposalStartupBinding(
                manager
            ).bind(
                provider_runtime=(
                    construction
                    .execution_dependency_assembly
                    .provider_runtime
                )
            )
        )

        construction.execution_dependency_assembly.bind_code_modification_proposal(
            proposal_capability
        )

        runtime = construction.create()
        workspace = construction.workspace

        execution = self.execution.create(
            runtime=runtime,
            workspace=workspace,
            manager=manager,
            capability_composition=capability_composition,
            planning_binding=planning_binding,
            tool_binding=tool_binding,
            project_session_operational=project_session_operational,
            context=context,
            planner=planner,
        )

        code_intelligence_binding.bind(
            runtime_port=ApplicationRuntimePortAdapter(runtime),
            capability_manager=manager,
        )

        gateway = execution["runtime_execution_gateway"]
        runtime_submission = (
            ApplicationRuntimeSubmissionFactory().create(
                gateway
            )
        )

        project_removal = (
            ApplicationProjectRemovalFactory().create(
                registration=project_registration,
                session_service=service,
            )
        )

        project_adapter = (
            ProjectSessionApplicationAdapterFactory().create(
                service
            )
        )

        integration = project_session_binding.start(
            runtime_submission=runtime_submission,
        )

        context.update(
            {
                "capability_manager": manager,
                "runtime_submission": runtime_submission,
                "planning_binding": planning_binding,
                "code_intelligence_binding": code_intelligence_binding,
                "tool_binding": tool_binding,
                "project_registry": project_registry,
                "project_session_service": service,
                "project_session_operational": project_session_operational,
                "project_registration": project_registration,
                "project_removal": project_removal,
                "project_session_application_adapter": project_adapter,
                "project_session_binding": project_session_binding,
                "project_session_integration": integration,
                "code_modification_proposal": proposal_capability,
            }
        )

        return {
            "context": context,
            "manager": manager,
            **execution,
            "runtime_submission": runtime_submission,
        }

    def ready(
        self,
    ) -> bool:
        return self.support.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution": self.execution.dump(),
        }


__all__ = [
    "ApplicationStartupAssemblyBuilder",
]
