from __future__ import annotations

from backend.application.composition.agent import (
    ApplicationAgentComposition,
)
from backend.application.composition.agent_composition_builder import (
    ApplicationAgentCompositionBuilder,
)
from backend.application.composition.agent_composition_builder_contract import (
    ApplicationAgentCompositionBuilderProtocol,
)
from backend.application.composition.agent_composition_builder_support import (
    ApplicationAgentCompositionBuilderSupport,
)
from backend.application.composition.agent_input_validator import (
    ApplicationAgentInputValidator,
)


class ApplicationAgentCompositionFactory:
    """
    Sole construction owner for ApplicationAgentComposition.
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        input_validator: (
            ApplicationAgentInputValidator | None
        ) = None,
        builder: (
            ApplicationAgentCompositionBuilderProtocol | None
        ) = None,
        builder_support: (
            ApplicationAgentCompositionBuilderSupport | None
        ) = None,
    ) -> ApplicationAgentComposition:
        active_validator = (
            input_validator
            or ApplicationAgentInputValidator()
        )

        if not isinstance(
            active_validator,
            ApplicationAgentInputValidator,
        ):
            raise TypeError(
                "input validator must "
                "ApplicationAgentInputValidator"
            )

        active_builder = builder

        if active_builder is None:
            active_builder = ApplicationAgentCompositionBuilder(
                support=builder_support,
            )

        if not isinstance(
            active_builder,
            ApplicationAgentCompositionBuilderProtocol,
        ):
            raise TypeError(
                "builder must implement "
                "ApplicationAgentCompositionBuilderProtocol"
            )

        composition = ApplicationAgentComposition(
            input_validator=active_validator,
            builder=active_builder,
        )

        if not composition.ready():
            raise RuntimeError(
                "application agent composition unavailable"
            )

        return composition

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
    "ApplicationAgentCompositionFactory",
]
