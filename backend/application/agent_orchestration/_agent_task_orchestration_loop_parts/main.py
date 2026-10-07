"""Main class AgentTaskOrchestrationLoop."""
from __future__ import annotations
from .part1 import AgentTaskOrchestrationLoopContract  # noqa
from .mixin1 import _Mixin1

class AgentTaskOrchestrationLoop(_Mixin1, AgentTaskOrchestrationLoopContract):

    """
    Application bounded autonomous task loop.

    Each iteration enters AgentTaskOrchestrator once.
    The orchestrator performs execution and records the
    corresponding decision. The loop consumes that decision
    exactly once for terminal/iteration transition.
    """
    VERSION = "1.2"
