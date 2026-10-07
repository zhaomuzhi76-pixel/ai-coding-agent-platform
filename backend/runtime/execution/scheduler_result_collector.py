from __future__ import annotations


from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)



class SchedulerResultCollector:
    """
    Collect scheduler execution results.


    Responsibility:
        - preserve node execution results
        - provide scheduler result boundary


    Not Responsible:
        - output extraction
        - state mutation
        - persistence
    """


    VERSION = "2.0"



    def collect(
        self,
        results: list[NodeExecutionResult],
    ) -> list[NodeExecutionResult]:


        if not isinstance(
            results,
            list,
        ):
            raise TypeError(
                "results must list"
            )


        for result in results:

            if not isinstance(
                result,
                NodeExecutionResult,
            ):
                raise TypeError(
                    "result must NodeExecutionResult"
                )


        return results



    def ready(
        self,
    ) -> bool:

        return True



__all__ = [
    "SchedulerResultCollector",
]
