from __future__ import annotations
from typing import Any
from backend.application.capability.tool_adapter_factory import ToolApplicationCapabilityAdapterFactory
from backend.application.context.application_context_factory import ApplicationContextFactory
from backend.application.composition.agent_factory import ApplicationAgentCompositionFactory
from backend.application.composition.capability import ApplicationCapabilityComposition
from backend.application.operational.project_session.project_session_operational_contract import ProjectSessionOperationalContract
from backend.core.execution.execution_flow_protocol import ExecutionFlowProtocol
from backend.application.operational.runtime_execution_session.runtime_execution_session_flow_factory import RuntimeExecutionSessionFlowFactory
from backend.application.planning.composition_factory import PlanningApplicationCompositionFactory
from backend.application.planning.execution_preparer_factory import PlanningExecutionPreparerFactory
from backend.application.planning.startup_binding import PlanningStartupBinding
from backend.application.tool.service_factory import (
    ToolApplicationServiceFactory,
)
from backend.application.composition.runtime_port import (
    ApplicationRuntimePortProtocol,
)
from backend.application.composition.runtime_port_adapter import (
    ApplicationRuntimePortAdapter,
)
from backend.application.composition.workspace_tool_runtime import (
    ApplicationWorkspaceToolRuntime,
)
from backend.application.tool.startup_binding import ToolApplicationStartupBinding

class ApplicationStartupExecutionAssembly:
    VERSION = '2.1'

    def create(self, *, runtime: Any, workspace: Any, manager: Any, capability_composition: ApplicationCapabilityComposition, planning_binding: PlanningStartupBinding, tool_binding: ToolApplicationStartupBinding, project_session_operational: ProjectSessionOperationalContract, context: dict[str, Any], planner: Any) -> dict[str, Any]:
        runtime_port = ApplicationRuntimePortAdapter(runtime)
        self._validate(
            runtime_port,
            workspace,
            manager,
            project_session_operational,
            context,
            planner,
        )
        default_workspace = getattr(
            workspace,
            "root_path",
            None,
        )
        if not isinstance(default_workspace, str) or not default_workspace.strip():
            raise RuntimeError(
                "startup workspace root unavailable"
            )

        tool_runtime = ApplicationWorkspaceToolRuntime(
            runtime=runtime_port,
            default_workspace=default_workspace,
        )
        tool_service = ToolApplicationServiceFactory().create(
            capability=tool_runtime,
        )
        tool_capability = ToolApplicationCapabilityAdapterFactory().create(service=tool_service)
        tool_binding.bind(capability_manager=manager, capability=tool_capability)
        planning_composition = PlanningApplicationCompositionFactory().create()
        planning_service = planning_composition.create(planner=planner)
        planning_binding.bind(planning_service=planning_service, capability_manager=manager)
        execution_preparer = PlanningExecutionPreparerFactory().create(planning_service=planning_service)
        engine = runtime_port.create_execution_engine()
        runtime_flow = runtime_port.create_runtime_flow(preparer=execution_preparer, executor=engine)
        if not isinstance(runtime_flow, ExecutionFlowProtocol):
            raise TypeError('runtime application flow must implement ExecutionFlowProtocol')
        session_flow = RuntimeExecutionSessionFlowFactory().create(
            operational=project_session_operational,
            runtime_flow=runtime_flow,
        )
        project_session_service = context.get('project_session_service')
        if project_session_service is None:
            raise RuntimeError('project session service required')
        if project_session_operational is None:
            raise ValueError('project session operational required')
        if not project_session_operational.ready():
            raise RuntimeError('project session operational unavailable')
        agent_result = (
            ApplicationAgentCompositionFactory()
            .create()
            .create(

                runtime=runtime_port,
                runtime_execution_session_flow=session_flow,
                context_factory=ApplicationContextFactory(),
            )
        )
        capability_composition.install_agent(manager, agent_result['agent_service'])
        result = {'runtime': runtime, 'planner': planner, 'planning_service': planning_service, 'execution_preparer': execution_preparer, **agent_result}
        context.update(result)
        return result

    @staticmethod
    def _validate(
        runtime_port: ApplicationRuntimePortProtocol,
        workspace: Any,
        manager: Any,
        project_session_operational: ProjectSessionOperationalContract,
        context: dict[str, Any],
        planner: Any,
    ) -> None:
        if not isinstance(
            runtime_port,
            ApplicationRuntimePortProtocol,
        ):
            raise TypeError("runtime port contract required")
        if not runtime_port.ready():
            raise RuntimeError("runtime port unavailable")
        if workspace is None:
            raise ValueError("workspace required")
        if manager is None:
            raise ValueError("capability manager required")
        if not isinstance(context, dict):
            raise TypeError("startup context must dict")
        if planner is None:
            raise ValueError("planner required")
        if not isinstance(
            project_session_operational,
            ProjectSessionOperationalContract,
        ):
            raise TypeError(
                "project session operational contract required"
            )
        if not project_session_operational.ready():
            raise RuntimeError(
                "project session operational unavailable"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {'name': type(self).__name__, 'version': self.VERSION, 'ready': self.ready()}
__all__ = ['ApplicationStartupExecutionAssembly']
