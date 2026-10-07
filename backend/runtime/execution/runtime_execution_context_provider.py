from __future__ import annotations


from backend.runtime.execution.runtime_execution_context import (
    RuntimeExecutionContext,
)


from backend.runtime.execution.runtime_execution_state_factory import (
    RuntimeExecutionStateFactory,
)



class RuntimeExecutionContextProvider:
    """
    Runtime execution context provider.


    Responsibility:

        - create runtime execution context
        - assemble state factory dependency


    Not Responsible:

        - execution
        - scheduling
        - persistence
    """


    VERSION = "2.0"



    def create_factory(
        self,
    ) -> RuntimeExecutionStateFactory:

        return RuntimeExecutionStateFactory()



    def create(
        self,
    ) -> RuntimeExecutionContext:

        return RuntimeExecutionContext(
            factory=(
                self.create_factory()
            )
        )



    def ready(
        self,
    ) -> bool:

        return True



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }



__all__ = [
    "RuntimeExecutionContextProvider",
]
