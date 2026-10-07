from __future__ import annotations
from typing import Any
from backend.application.composition.capability import ApplicationCapabilityComposition
from backend.application.composition.project_session import ApplicationProjectSessionComposition
from backend.application.modules.registry import ApplicationModuleRegistry
from backend.application.operational.project_session.project_session_operational_contract import ProjectSessionOperationalContract
from backend.application.operational.project_session.startup import ProjectSessionStartupBinding
from backend.application.planning.startup_binding import PlanningStartupBinding
from backend.application.startup_assembly_builder import ApplicationStartupAssemblyBuilder
from backend.application.startup_assembly_support import ApplicationStartupAssemblySupport
from backend.application.tool.startup_binding import ToolApplicationStartupBinding
from backend.core.planning import PlannerPortProtocol

class ApplicationStartupAssembly:
    """
    Application startup dependency assembly boundary.

    Owns:
        - delegation to the dedicated assembly builder
        - assembly support lifecycle

    Does not own:
        - runtime/session implementation
        - startup state
        - startup lifecycle
        - transport
    """
    VERSION = '2.4'

    def __init__(self, support: ApplicationStartupAssemblySupport | None=None, builder: ApplicationStartupAssemblyBuilder | None=None) -> None:
        self.support = support or ApplicationStartupAssemblySupport()
        self.builder = builder or ApplicationStartupAssemblyBuilder(self.support)

    def build(self, *, registry: ApplicationModuleRegistry, capability_composition: ApplicationCapabilityComposition, planning_binding: PlanningStartupBinding, code_intelligence_binding: Any, tool_binding: ToolApplicationStartupBinding, project_session_composition: ApplicationProjectSessionComposition, project_session_operational: ProjectSessionOperationalContract, project_session_binding: ProjectSessionStartupBinding, project_registry: Any, project_registration: Any, planner: PlannerPortProtocol) -> dict[str, Any]:
        return self.builder.build(registry=registry, capability_composition=capability_composition, planning_binding=planning_binding, code_intelligence_binding=code_intelligence_binding, tool_binding=tool_binding, project_session_composition=project_session_composition, project_session_operational=project_session_operational, project_session_binding=project_session_binding, project_registry=project_registry, project_registration=project_registration, planner=planner)

    def ready(self) -> bool:
        return self.support.ready() and self.builder.ready()

    def dump(self) -> dict[str, object]:
        return {'name': type(self).__name__, 'version': self.VERSION, 'ready': self.ready(), 'builder': self.builder.dump()}
__all__ = ['ApplicationStartupAssembly']
