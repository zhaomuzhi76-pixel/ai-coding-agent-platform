from __future__ import annotations


from backend.runtime.execution.dag_execution_progress import (
    DAGExecutionProgress,
)


class DAGCycleProgressTracker:
    """
    DAG cycle progress observation.

    Responsibility:
        - capture before/after state
        - detect stalled execution

    Not Responsible:
        - execution
        - scheduling
        - state mutation
    """


    VERSION = "1.0"


    def __init__(
        self,
        progress: DAGExecutionProgress,
    ) -> None:

        if progress is None:
            raise ValueError(
                "progress required"
            )

        self.progress = progress



    def before(
        self,
        state,
    ):

        return state.snapshot()



    def after(
        self,
        state,
    ):

        return state.snapshot()



    def check(
        self,
        before,
        after,
    ) -> None:

        self.progress.check(
            before,
            after,
        )



    def ready(
        self,
    ) -> bool:

        return self.progress.ready()



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name":
                "DAGCycleProgressTracker",
            "version":
                self.VERSION,
            "ready":
                self.ready(),
        }



__all__ = [
    "DAGCycleProgressTracker",
]
