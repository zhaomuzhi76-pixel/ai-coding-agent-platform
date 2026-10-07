from __future__ import annotations

from backend.application.composition.runtime_construction_port import (
    ApplicationRuntimeConstructionProtocol,
)
from backend.application.composition.project_session_construction_port import (
    ApplicationProjectSessionConstructionProtocol,
)
from backend.core.planning import PlannerPortProtocol
from backend.application.startup import (
    ApplicationStartup,
)
from backend.application.startup_composition_factory import (
    ApplicationStartupCompositionFactory,
)


class ApplicationStartupFactory:
    """
    Final construction owner for ApplicationStartup.

    Owns only:
        - dependency composition
        - facade construction
        - lifecycle construction
        - construction-time validation
    """

    VERSION = "2.2"

    def __init__(
        self,
        *,
        runtime_construction: ApplicationRuntimeConstructionProtocol,
        planner: PlannerPortProtocol,
        project_session_construction: (
            ApplicationProjectSessionConstructionProtocol
        ),
        composition_factory: (
            ApplicationStartupCompositionFactory
            | None
        ) = None,
    ) -> None:
        if not isinstance(
            runtime_construction,
            ApplicationRuntimeConstructionProtocol,
        ):
            raise TypeError(
                "runtime_construction must implement "
                "ApplicationRuntimeConstructionProtocol"
            )

        if not runtime_construction.ready():
            raise RuntimeError(
                "runtime construction unavailable"
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

        if not isinstance(
            project_session_construction,
            ApplicationProjectSessionConstructionProtocol,
        ):
            raise TypeError(
                "project session construction contract required"
            )

        if not project_session_construction.ready():
            raise RuntimeError(
                "project session construction unavailable"
            )

        self.runtime_construction = runtime_construction
        self.planner = planner
        self.project_session_construction = (
            project_session_construction
        )
        self.composition_factory = (
            composition_factory
            or ApplicationStartupCompositionFactory()
        )

    def create(self) -> ApplicationStartup:
        if not self.ready():
            raise RuntimeError(
                "application startup factory unavailable"
            )

        dependencies = self.composition_factory.create(
            runtime_construction=self.runtime_construction,
            planner=self.planner,
            project_session_construction=(
                self.project_session_construction
            ),
        )

        state = dependencies.get("state")

        if state is None:
            raise RuntimeError(
                "application startup state required"
            )

        
        startup = ApplicationStartup(
            **dependencies,
            lifecycle=None,
        )

        startup.lifecycle = (
            self.composition_factory.create_lifecycle(
                startup
            )
        )

        if startup.lifecycle is None:
            raise RuntimeError(
                "application startup lifecycle unavailable"
            )

        return startup

    def ready(self) -> bool:
        return (
            self.runtime_construction.ready()
            and self.project_session_construction.ready()
            and self.composition_factory is not None
            and self.composition_factory.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "runtime_construction": type(
                self.runtime_construction
            ).__name__,
            "composition_factory": (
                self.composition_factory.dump()
            ),
        }


__all__ = [
    "ApplicationStartupFactory",
]
