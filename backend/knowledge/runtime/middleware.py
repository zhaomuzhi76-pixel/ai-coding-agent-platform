from __future__ import annotations

from backend.core.agent.agent_middleware_protocol import (
    AgentMiddlewareProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.context.context_protocol import ContextProtocol
from backend.core.contracts.value import CoreValue
from backend.core.execution.execution_request_protocol import (
    ExecutionRequestProtocol,
)
from backend.knowledge.runtime.injector import KnowledgeInjector
from backend.knowledge.runtime.learning_bridge import (
    KnowledgeLearningBridge,
)


class KnowledgeMiddleware(AgentMiddlewareProtocol):
    """
    Knowledge semantic middleware.

    Responsibility:
        - retrieve knowledge before execution
        - persist classified request knowledge after success

    Not Responsible:
        - middleware construction
        - knowledge storage
        - ranking
        - planning
        - runtime execution
    """

    VERSION = "2.0"
    RESPONSIBILITY = (
        "knowledge_semantic_middleware",
    )

    def __init__(
        self,
        injector: KnowledgeInjector,
        learning_bridge: KnowledgeLearningBridge,
        *,
        priority: int = 20,
        enabled: bool = True,
    ) -> None:
        if injector is None:
            raise ValueError(
                "knowledge injector required"
            )

        if learning_bridge is None:
            raise ValueError(
                "knowledge learning bridge required"
            )

        if not injector.ready():
            raise RuntimeError(
                "knowledge injector not ready"
            )

        if not learning_bridge.ready():
            raise RuntimeError(
                "knowledge learning bridge not ready"
            )

        self.name = "knowledge"
        self.priority = priority
        self.enabled = enabled
        self.injector = injector
        self.learning_bridge = learning_bridge
        self.inject_count = 0
        self.learn_count = 0

    async def on_start(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
    ) -> None:
        self._validate(request, context)

    async def before(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
    ) -> None:
        self._validate(request, context)

        agent_request = self._agent_request(request)

        self.injector.inject(
            agent_request.message,
            context,
        )
        self.inject_count += 1

    async def after(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
        result: CoreValue,
    ) -> CoreValue:
        return result

    async def on_success(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
        result: CoreValue,
    ) -> None:
        self._validate(request, context)

        agent_request = self._agent_request(request)
        item = self.learning_bridge.learn_from_request(
            agent_request
        )

        if item is not None:
            self.learn_count += 1

        context.set(
            "knowledge.learned",
            (
                [
                    item.item_id or "",
                    item.content,
                    str(item.knowledge_type),
                ]
                if item is not None
                else None
            ),
        )

    async def on_failure(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
        error: Exception,
    ) -> None:
        self._validate(request, context)

    async def on_finish(
        self,
        context: ContextProtocol,
        request: ExecutionRequestProtocol,
    ) -> None:
        self._validate(request, context)

    def is_enabled(
        self,
    ) -> bool:
        return bool(self.enabled)

    def ready(
        self,
    ) -> bool:
        return (
            self.is_enabled()
            and self.injector.ready()
            and self.learning_bridge.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "priority": self.priority,
            "enabled": self.enabled,
            "ready": self.ready(),
            "inject_count": self.inject_count,
            "learn_count": self.learn_count,
            "injector": self.injector.dump(),
            "learning_bridge": (
                self.learning_bridge.dump()
            ),
        }

    @staticmethod
    def _validate(
        request: ExecutionRequestProtocol,
        context: ContextProtocol,
    ) -> None:
        if request is None or not isinstance(
            request,
            ExecutionRequestProtocol,
        ):
            raise TypeError(
                "request must implement ExecutionRequestProtocol"
            )

        if context is None or not isinstance(
            context,
            ContextProtocol,
        ):
            raise TypeError(
                "context must implement ContextProtocol"
            )

        if not context.ready():
            raise RuntimeError(
                "middleware context not ready"
            )

    @staticmethod
    def _agent_request(
        request: ExecutionRequestProtocol,
    ) -> AgentRequest:
        if not isinstance(request, AgentRequest):
            raise TypeError(
                "knowledge middleware requires AgentRequest"
            )
        if not request.ready():
            raise ValueError("agent request not ready")

        return request


__all__ = [
    "KnowledgeMiddleware",
]
