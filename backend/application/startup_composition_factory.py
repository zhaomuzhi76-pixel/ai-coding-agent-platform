from __future__ import annotations
from backend.application.capability.manager_factory import ApplicationCapabilityManagerFactory
from backend.application.capability.registry_factory import ApplicationCapabilityRegistryFactory
from backend.application.capability.tool_composition_factory import ApplicationToolCompositionFactory
from backend.application.code_intelligence.startup_binding import CodeIntelligenceStartupBinding
from backend.application.composition.capability import ApplicationCapabilityComposition
from backend.application.composition.capability_factory import ApplicationCapabilityCompositionFactory
from backend.application.composition.project_session import ApplicationProjectSessionComposition
from backend.application.composition.project_session_construction_port import ApplicationProjectSessionConstructionProtocol
from backend.application.composition.runtime_construction_port import ApplicationRuntimeConstructionProtocol
from backend.application.modules.registry_factory import ApplicationModuleRegistryFactory
from backend.application.operational.project_session.project_session_operational_factory import ProjectSessionOperationalFactory
from backend.application.operational.project_session.startup import ProjectSessionStartupBindingFactory
from backend.application.planning.startup_binding import PlanningStartupBinding
from backend.application.project.project_registration_factory import ApplicationProjectRegistrationFactory
from backend.persistence.plugins.project_session_persistence_composition_factory import ProjectSessionPersistenceCompositionFactory
from backend.persistence.plugins.project_session_persistence_adapter import ProjectSessionPersistenceAdapter
from backend.application.startup_assembly import ApplicationStartupAssembly
from backend.application.startup_accessors import ApplicationStartupAccessors
from backend.application.startup_composition_support import ApplicationStartupCompositionSupport
from backend.application.startup_lifecycle import ApplicationStartupLifecycle
from backend.application.startup_state import ApplicationStartupState
from backend.application.tool.startup_binding import ToolApplicationStartupBinding
from backend.core.planning import PlannerPortProtocol

class ApplicationStartupCompositionFactory:
    """Own construction of the ApplicationStartup graph."""
    VERSION = '1.2'

    def create(self, *, runtime_construction: ApplicationRuntimeConstructionProtocol, planner: PlannerPortProtocol, project_session_construction: ApplicationProjectSessionConstructionProtocol) -> dict[str, object]:
        self._validate_runtime(runtime_construction)
        self._validate_planner(planner)
        self._validate_project_session(project_session_construction)
        project_session_result = project_session_construction.create()
        session_persistence = ProjectSessionPersistenceCompositionFactory().create()
        session_service = project_session_result['session_service']
        session_adapter = ProjectSessionPersistenceAdapter(
            service=session_service,
            persistence=session_persistence.repository,
        )
        project_session_result = dict(project_session_result)
        project_session_result['session_persistence'] = session_persistence
        project_session_result['session_service'] = session_adapter
        project_session = ApplicationProjectSessionComposition(assembly=project_session_result)
        project_registry = project_session_result['project_registry']
        project_factory = project_session_result['project_factory']
        registration_factory = ApplicationProjectRegistrationFactory()
        project_registration = registration_factory.create(project_registry, project_factory)
        project_session_operational = ProjectSessionOperationalFactory().create(project_session_result['session_service'])
        capability_registry = ApplicationCapabilityRegistryFactory().create()
        registry = ApplicationModuleRegistryFactory(capability_registry=capability_registry, runtime_construction=runtime_construction).create()
        capability_manager = ApplicationCapabilityManagerFactory().create(registry=capability_registry)
        capability = ApplicationCapabilityCompositionFactory().create()
        state = ApplicationStartupState()
        dependencies = {'registry': registry, 'planner': planner, 'capability_composition': capability, 'project_session_composition': project_session, 'project_registry': project_registry, 'project_session_operational': project_session_operational, 'project_registration_factory': registration_factory, 'project_registration': project_registration, 'assembly': ApplicationStartupAssembly(), 'state': state, 'accessors': ApplicationStartupAccessors(), 'planning_binding': PlanningStartupBinding(), 'code_intelligence_binding': CodeIntelligenceStartupBinding(capability_manager), 'tool_binding': ToolApplicationStartupBinding(ApplicationToolCompositionFactory().create(manager=capability_manager)), 'project_session_binding': ProjectSessionStartupBindingFactory().create(project_session_operational)}
        ApplicationStartupCompositionSupport.validate(dependencies)
        return dependencies

    def create_lifecycle(self, owner: object) -> ApplicationStartupLifecycle:
        accessors = getattr(owner, 'accessors', None)
        if not isinstance(accessors, ApplicationStartupAccessors):
            raise TypeError('application startup accessors invalid')
        return ApplicationStartupLifecycle(owner, accessors)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {'name': type(self).__name__, 'version': self.VERSION, 'ready': self.ready()}

    @staticmethod
    def _validate_runtime(runtime_construction: object) -> None:
        if not isinstance(runtime_construction, ApplicationRuntimeConstructionProtocol):
            raise TypeError('runtime construction contract required')
        if not runtime_construction.ready():
            raise RuntimeError('runtime construction unavailable')

    @staticmethod
    def _validate_planner(planner: object) -> None:
        if not isinstance(planner, PlannerPortProtocol):
            raise TypeError('planner must implement PlannerPortProtocol')
        if not planner.ready():
            raise RuntimeError('planner unavailable')

    @staticmethod
    def _validate_project_session(construction: object) -> None:
        if not isinstance(construction, ApplicationProjectSessionConstructionProtocol):
            raise TypeError('project session construction contract required')
        if not construction.ready():
            raise RuntimeError('project session construction unavailable')
__all__ = ['ApplicationStartupCompositionFactory']
