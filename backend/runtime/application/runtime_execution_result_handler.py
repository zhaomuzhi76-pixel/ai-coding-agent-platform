from __future__ import annotations


from backend.runtime.application.runtime_execution_flow_validator import (
    RuntimeExecutionFlowValidator,
)



class RuntimeExecutionResultHandler:
    """
    Runtime execution result boundary.


    Responsibility:
        - validate execution result


    Not Responsible:
        - execution
        - persistence
    """


    VERSION = "1.0"



    def __init__(
        self,
        validator: RuntimeExecutionFlowValidator,
    ) -> None:

        self.validator = validator



    def handle(
        self,
        outputs: list[object],
    ) -> list[object]:

        self.validator.validate_outputs(
            outputs
        )

        return outputs



    def ready(
        self,
    ) -> bool:

        return self.validator.ready()



__all__ = [
    "RuntimeExecutionResultHandler",
]
