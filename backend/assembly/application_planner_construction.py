from __future__ import annotations

from pathlib import Path

from backend.agent.planner.planner_engine_factory import (
    PlannerEngineFactory,
)
from backend.agent.planner.planner_port_adapter import (
    PlannerPortAdapter,
)
from backend.code_intelligence.composition import (
    CodeIntelligenceComposition,
)
from backend.core.planning import PlannerPortProtocol
from backend.core.planning.intelligence_port import (
    PlannerIntelligenceProtocol,
)


class ApplicationPlannerConstruction:
    """
    Assembly-root planner construction boundary.

    Planner consumes the Core intelligence port.
    Concrete intelligence construction stays in Code Intelligence.
    """

    VERSION = "2.0"

    def __init__(
        self,
        *,
        workspace_root: str,
        factory: PlannerEngineFactory | None = None,
        intelligence: PlannerIntelligenceProtocol | None = None,
    ) -> None:
        if (
            not isinstance(
                workspace_root,
                str,
            )
            or not workspace_root.strip()
        ):
            raise ValueError(
                "workspace root required"
            )

        self.workspace_root = str(
            Path(workspace_root)
            .expanduser()
            .resolve()
        )
        self.factory = (
            factory
            if factory is not None
            else PlannerEngineFactory()
        )
        self.intelligence = (
            intelligence
            if intelligence is not None
            else CodeIntelligenceComposition(
                workspace=self.workspace_root,
            ).create()
        )

        if not isinstance(
            self.intelligence,
            PlannerIntelligenceProtocol,
        ):
            raise TypeError(
                "planner intelligence contract required"
            )

    def create(self) -> PlannerPortProtocol:
        if not self.ready():
            raise RuntimeError(
                "planner construction unavailable"
            )

        engine = self.factory.create(
            intelligence=self.intelligence,
        )
        planner = PlannerPortAdapter(
            engine=engine,
        )

        if not isinstance(
            planner,
            PlannerPortProtocol,
        ):
            raise TypeError(
                "planner must implement PlannerPortProtocol"
            )

        if not planner.ready():
            raise RuntimeError(
                "planner unavailable"
            )

        return planner

    def ready(self) -> bool:
        return (
            self.factory.ready()
            and self.intelligence.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "workspace_root": self.workspace_root,
            "factory": type(
                self.factory
            ).__name__,
            "intelligence": type(
                self.intelligence
            ).__name__,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPlannerConstruction",
]
