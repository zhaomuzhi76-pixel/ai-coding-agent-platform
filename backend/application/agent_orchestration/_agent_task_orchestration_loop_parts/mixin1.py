"""Mixin 1 of AgentTaskOrchestrationLoop."""
from __future__ import annotations
from .part1 import (AgentDecision, AgentOrchestrationLoopState, AgentOrchestrationProtocol, AgentRequest, AgentTaskOrchestrationLoopSupport, AgentTaskOrchestrator, ExecutionResult,)  # noqa: F401
class _Mixin1:
    def __init__(
        self,
        *,
        orchestrator: AgentTaskOrchestrator,
        max_iterations: int = 3,
        support: AgentTaskOrchestrationLoopSupport | None = None,
    ) -> None:
        if not isinstance(
            orchestrator,
            AgentOrchestrationProtocol,
        ):
            raise TypeError(
                "orchestrator must implement "
                "AgentOrchestrationProtocol"
            )

        if max_iterations < 1:
            raise ValueError(
                "max_iterations must be >= 1"
            )

        self.orchestrator = orchestrator
        self.max_iterations = max_iterations
        self.support = (
            support
            or AgentTaskOrchestrationLoopSupport()
        )
        self._state = self.support.initial(
            max_iterations
        )
        self._decision: AgentDecision | None = None
        self.execution_count = 0

    async def execute(
        self,
        *,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
        self.support.validate(
            request,
            session_id,
            self.max_iterations,
        )

        self._state = self.support.initial(
            self.max_iterations
        )
        self._decision = None

        result: ExecutionResult | None = None

        while not self._state.terminal:
            result = await self.orchestrator.execute(
                request=request,
                session_id=session_id,
            )
            result = self.support.require_result(result)

            decision = self.orchestrator.last_decision
            decision = self.support.require_decision(
                decision
            )

            self.execution_count += 1

            next_state = self.transition(
                decision=decision
            )

            if (
                not decision.terminal
                and next_state.terminal
                and next_state.iteration
                >= next_state.max_iterations
            ):
                decision = (
                    self.orchestrator
                    .terminate_for_iteration_limit()
                )

            self._decision = decision
            self._state = next_state

        if result is None:
            raise RuntimeError(
                "orchestration loop produced no result"
            )

        return result

    def decide(
        self,
        *,
        request: AgentRequest,
        result: ExecutionResult,
    ) -> AgentDecision:
        decision = self.orchestrator.decide(
            request=request,
            result=result,
        )
        return self.support.require_decision(
            decision
        )

    def state(
        self,
    ) -> AgentOrchestrationLoopState:
        return self._state

    def transition(
        self,
        *,
        decision: AgentDecision,
    ) -> AgentOrchestrationLoopState:
        decision = self.support.require_decision(
            decision
        )

        if decision.terminal:
            return self._state.finish()

        next_iteration = (
            self._state.iteration + 1
        )

        if next_iteration >= (
            self._state.max_iterations
        ):
            return AgentOrchestrationLoopState(
                iteration=self._state.max_iterations,
                max_iterations=self._state.max_iterations,
                terminal=True,
            )

        return self._state.next()

    def terminal(
        self,
    ) -> bool:
        return self._state.terminal

    def last_decision(
        self,
    ) -> AgentDecision | None:
        return self._decision

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and self.orchestrator.ready()
            and self._state.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "max_iterations": self.max_iterations,
            "execution_count": self.execution_count,
            "state": self._state.dump(),
            "last_decision": (
                self._decision.dump()
                if self._decision is not None
                else None
            ),
            "orchestrator": type(
                self.orchestrator
            ).__name__,
        }
