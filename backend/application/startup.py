from __future__ import annotations
from typing import TYPE_CHECKING, Any
from backend.application.capability.manager import ApplicationCapabilityManager
from backend.application.startup_accessors import ApplicationStartupAccessors
from backend.application.startup_lifecycle import ApplicationStartupLifecycle
from backend.application.startup_state import ApplicationStartupState
from backend.application.startup_support import ApplicationStartupSupport
if TYPE_CHECKING:
    from backend.application.capability.planning_composition import ApplicationPlanningCapabilityComposition
    from backend.application.code_intelligence.startup_binding import CodeIntelligenceStartupBinding
    from backend.application.composition.capability import ApplicationCapabilityComposition
    from backend.application.composition.project_session import ApplicationProjectSessionComposition
    from backend.application.modules.registry import ApplicationModuleRegistry
    from backend.application.operational.project_session.project_session_operational_contract import ProjectSessionOperationalContract
    from backend.application.operational.project_session.startup import ProjectSessionStartupBinding
    from backend.application.planning.startup_binding import PlanningStartupBinding
    from backend.application.project.project_registration import ApplicationProjectRegistration
    from backend.application.project.project_registration_factory import ApplicationProjectRegistrationFactory
    from backend.application.startup_assembly import ApplicationStartupAssembly
    from backend.application.tool.startup_binding import ToolApplicationStartupBinding

class ApplicationStartup:
    """
    Public startup facade over an already-composed dependency graph.

    Owns only:
        - dependency identity
        - public startup API
        - lifecycle delegation

    Does not own dependency construction.
    """
    VERSION = '12.1'

    def __init__(self, *, registry: ApplicationModuleRegistry, capability_composition: ApplicationCapabilityComposition, project_session_composition: ApplicationProjectSessionComposition, project_session_operational: ProjectSessionOperationalContract, project_registry: object, project_registration_factory: ApplicationProjectRegistrationFactory, project_registration: ApplicationProjectRegistration, assembly: ApplicationStartupAssembly, state: ApplicationStartupState, accessors: ApplicationStartupAccessors, planning_binding: PlanningStartupBinding, code_intelligence_binding: CodeIntelligenceStartupBinding, tool_binding: ToolApplicationStartupBinding, project_session_binding: ProjectSessionStartupBinding, planner: Any,
        lifecycle: ApplicationStartupLifecycle | None=None) -> None:
        self.registry = registry
        self.capability_composition = capability_composition
        self.project_session_composition = project_session_composition
        self.project_session_operational = project_session_operational
        self.project_registry = project_registry
        self.project_registration_factory = project_registration_factory
        self.project_registration = project_registration
        self.assembly = assembly
        self.state = state
        self.accessors = accessors
        self.planning_binding = planning_binding
        self.code_intelligence_binding = code_intelligence_binding
        self.tool_binding = tool_binding
        self.project_session_binding = project_session_binding
        self._planner = planner
        self.lifecycle = lifecycle

    @property
    def runtime(self) -> Any:
        return self.accessors.runtime(self.state)

    @property
    def agent_service(self) -> Any:
        return self.accessors.agent_service(self.state)

    @property
    def planner(self) -> Any:
        return self._planner

    @property
    def runtime_submission(self) -> Any:
        return self.accessors.runtime_submission(self.state)

    @property
    def execution_gateway(self) -> Any:
        return self.accessors.execution_gateway(self.state)

    @property
    def event_bus(self) -> Any:
        return self.accessors.event_bus(self.state)

    @property
    def capability_manager(self) -> ApplicationCapabilityManager | None:
        return self.accessors.capability_manager(self.state)

    @property
    def started(self) -> bool:
        return self.accessors.started(self.state)

    def start(self) -> None:
        if self.lifecycle is None:
            raise RuntimeError('application startup lifecycle unavailable')
        self.lifecycle.start()

    def ready(self) -> bool:
        return self.lifecycle is not None and self.lifecycle.ready()

    def stop(self) -> None:
        if self.lifecycle is not None:
            self.lifecycle.stop()

    def dump(self) -> dict[str, object]:
        result = self.state.dump()
        result.update(ApplicationStartupSupport.dump(name=type(self).__name__, version=self.VERSION, started=self.started, runtime=self.runtime, capability_manager=self.capability_manager, planning_binding=self.planning_binding, code_intelligence_binding=self.code_intelligence_binding, tool_binding=self.tool_binding, registry=self.registry, ready=self.ready()))
        result['lifecycle'] = self.lifecycle.dump() if self.lifecycle is not None else None
        result['project_registration'] = self.project_registration.dump()
        return result
__all__ = ['ApplicationStartup']
