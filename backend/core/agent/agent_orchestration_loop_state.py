from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentOrchestrationLoopState:
    """
    Core-owned bounded orchestration loop state.

    Owns:
        - current iteration
        - maximum iteration boundary
        - terminal state

    Does not own:
        - planning
        - runtime execution
        - decision generation
    """

    VERSION = "1.0"

    iteration: int = 0
    max_iterations: int = 1
    terminal: bool = False

    def __post_init__(self) -> None:
        if self.iteration < 0:
            raise ValueError("iteration must be >= 0")

        if self.max_iterations < 1:
            raise ValueError(
                "max_iterations must be >= 1"
            )

        if self.iteration > self.max_iterations:
            raise ValueError(
                "iteration exceeds max_iterations"
            )

    @property
    def exhausted(self) -> bool:
        return (
            self.iteration
            >= self.max_iterations
        )

    @property
    def can_continue(self) -> bool:
        return (
            not self.terminal
            and not self.exhausted
        )

    def next(
        self,
        *,
        terminal: bool = False,
    ) -> "AgentOrchestrationLoopState":
        if self.terminal:
            raise RuntimeError(
                "loop already terminal"
            )

        if self.exhausted:
            raise RuntimeError(
                "loop iteration limit reached"
            )

        return AgentOrchestrationLoopState(
            iteration=self.iteration + 1,
            max_iterations=self.max_iterations,
            terminal=terminal,
        )

    def finish(
        self,
    ) -> "AgentOrchestrationLoopState":
        if self.terminal:
            return self

        return AgentOrchestrationLoopState(
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            terminal=True,
        )

    def ready(self) -> bool:
        return (
            self.iteration >= 0
            and self.max_iterations >= 1
            and self.iteration <= self.max_iterations
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "terminal": self.terminal,
            "exhausted": self.exhausted,
            "can_continue": self.can_continue,
            "ready": self.ready(),
        }


__all__ = [
    "AgentOrchestrationLoopState",
]
