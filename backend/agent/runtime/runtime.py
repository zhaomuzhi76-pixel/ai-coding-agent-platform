"""AgentRuntime: orchestrate roles over a blackboard."""
from __future__ import annotations

import asyncio
from typing import List, Optional

from backend.agent.runtime.blackboard import Blackboard
from backend.agent.runtime.message import AgentMessage
from backend.agent.runtime.role import RoleRegistry


class AgentRuntime:
    """Dispatch messages to roles, share blackboard, collect results."""

    def __init__(
        self,
        registry: RoleRegistry,
        blackboard: Optional[Blackboard] = None,
    ) -> None:
        self._registry = registry
        self._blackboard = blackboard or Blackboard()

    @property
    def registry(self) -> RoleRegistry:
        return self._registry

    @property
    def blackboard(self) -> Blackboard:
        return self._blackboard

    async def dispatch(
        self,
        role: str,
        message: AgentMessage,
    ) -> AgentMessage:
        agent = self._registry.get(role)
        self._blackboard.post(message)
        result = await agent.run(message, self._blackboard)
        self._blackboard.post(result)
        return result

    async def dispatch_many(
        self,
        plan: List[tuple],
    ) -> List[AgentMessage]:
        """Parallel: plan = [(role, AgentMessage), ...]"""
        coros = [self.dispatch(role, msg) for role, msg in plan]
        return list(await asyncio.gather(*coros))

    async def dispatch_chain(
        self,
        plan: List[tuple],
        initial_role: str,
        initial: AgentMessage,
    ) -> List[AgentMessage]:
        """Sequential: feed each step's output into next step."""
        results: List[AgentMessage] = []
        current_role = initial_role
        current_msg = initial
        for role, _ignored in plan:
            out = await self.dispatch(current_role, current_msg)
            results.append(out)
            current_role = role
            current_msg = out
        return results

    def ready(self) -> bool:
        return self._registry.ready()

    def dump(self) -> dict:
        return {
            "ready": self.ready(),
            "registry": self._registry.dump(),
            "blackboard": self._blackboard.dump(),
        }
