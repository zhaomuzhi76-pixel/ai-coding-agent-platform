from __future__ import annotations

from backend.application.agent_orchestration.agent_task_orchestration_loop import (
    AgentTaskOrchestrationLoop,
)
from backend.application.agent_orchestration.agent_task_orchestration_loop_support import (
    AgentTaskOrchestrationLoopSupport,
)
from backend.application.agent_orchestration.agent_task_orchestrator import (
    AgentTaskOrchestrator,
)


class AgentTaskOrchestrationLoopFactory:
    """
    Sole construction owner for AgentTaskOrchestrationLoop.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        orchestrator: AgentTaskOrchestrator,
        max_iterations: int = 3,
    ) -> AgentTaskOrchestrationLoop:
        loop = AgentTaskOrchestrationLoop(
            orchestrator=orchestrator,
            max_iterations=max_iterations,
            support=AgentTaskOrchestrationLoopSupport(),
        )

        if not loop.ready():
            raise RuntimeError(
                "agent task orchestration loop unavailable"
            )

        return loop

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskOrchestrationLoopFactory",
]
