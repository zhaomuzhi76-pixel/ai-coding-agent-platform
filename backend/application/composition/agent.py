from __future__ import annotations

from backend.application.composition.agent_composition_builder_contract import (
    ApplicationAgentCompositionBuilderProtocol,
)
from backend.application.composition.agent_input_validator import (
    ApplicationAgentInputValidator,
)
from backend.core.contracts.value import (
    CoreValue,
)


class ApplicationAgentComposition:
    """
    Application Agent composition boundary.

    Owns:
        - input validation
        - concrete builder delegation
        - result-shape validation

    Does not own:
        - runtime construction
        - kernel provider construction
        - middleware construction
        - gateway construction
        - Agent construction
        - Agent service construction
    """

    VERSION = "7.0"

    def __init__(
        self,
        input_validator: (
            ApplicationAgentInputValidator | None
        ) = None,
        builder: (
            ApplicationAgentCompositionBuilderProtocol
            | None
        ) = None,
    ) -> None:
        self.input_validator = (
            input_validator
            or ApplicationAgentInputValidator()
        )

        if not self.input_validator.ready():
            raise RuntimeError(
                "agent input validator unavailable"
            )

        if builder is None:
            raise ValueError(
                "agent composition builder required"
            )

        if not builder.ready():
            raise RuntimeError(
                "agent composition builder unavailable"
            )

        self.builder = builder

    def create(
        self,
        *,

        runtime: object,
        runtime_execution_session_flow: object,
        context_factory: object,
    ) -> dict[str, CoreValue]:
        self.input_validator.validate(

            runtime=runtime,
        )

        result = self.builder.create(

            runtime=runtime,
            runtime_execution_session_flow=runtime_execution_session_flow,
            context_factory=context_factory,
        )

        self._validate_result(result)
        return result

    def ready(
        self,
    ) -> bool:
        return (
            self.input_validator.ready()
            and self.builder.ready()
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "input_validator": (
                self.input_validator.dump()
            ),
            "builder": self.builder.dump(),
        }

    @staticmethod
    def _validate_result(
        result: dict[str, CoreValue],
    ) -> None:
        required = (

            "agent_service",
            "runtime_execution_gateway",
            "runtime_execution_session_flow_resolver",
        )

        missing = tuple(
            key
            for key in required
            if key not in result
        )

        if missing:
            raise RuntimeError(
                "agent composition result missing: "
                + ", ".join(missing)
            )


__all__ = [
    "ApplicationAgentComposition",
]
