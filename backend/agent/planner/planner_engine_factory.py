from __future__ import annotations

from backend.agent.planner.planner_engine import PlannerEngine
from backend.core.planning.intelligence_port import PlannerIntelligenceProtocol


class PlannerEngineFactory:
    """
    Construct the planner engine from Core-owned contracts.

    Intelligence implementation is supplied by the assembly root.
    """

    VERSION = "2.1"
    RESPONSIBILITY = ("planner_engine_construction",)

    def __init__(self) -> None:
        pass

    def create(
        self,
        *,
        intelligence: PlannerIntelligenceProtocol | None = None,
    ) -> PlannerEngine:
        if intelligence is not None:
            self._validate_intelligence(intelligence)

        engine = PlannerEngine(
            intelligence=intelligence,
        )

        if not engine.ready():
            raise RuntimeError(
                "planner engine unavailable"
            )

        return engine

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_intelligence(
        intelligence: object,
    ) -> None:
        if not isinstance(
            intelligence,
            PlannerIntelligenceProtocol,
        ):
            raise TypeError(
                "intelligence must implement "
                "PlannerIntelligenceProtocol"
            )
        if not intelligence.ready():
            raise RuntimeError(
                "planner intelligence unavailable"
            )


__all__ = ["PlannerEngineFactory"]
