from __future__ import annotations


from backend.runtime.execution.dag_iteration_policy import (
    DAGIterationPolicy,
)



class DAGLoopIterationController:
    """
    DAG loop iteration boundary.

    Responsibility:
        - maintain iteration count
        - validate iteration policy

    Not Responsible:
        - execution
        - completion
        - scheduling
    """


    VERSION = "1.0"


    def __init__(
        self,
        policy: DAGIterationPolicy,
    ) -> None:

        if policy is None:
            raise ValueError(
                "iteration policy required"
            )

        self.policy = policy

        self._iteration = 0



    def next(
        self,
    ) -> int:

        self._iteration += 1

        self.policy.validate(
            self._iteration
        )

        return self._iteration



    @property
    def current(
        self,
    ) -> int:

        return self._iteration



    def reset(
        self,
    ) -> None:

        self._iteration = 0



    def ready(
        self,
    ) -> bool:

        return self.policy.ready()



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name":
                "DAGLoopIterationController",

            "version":
                self.VERSION,

            "iteration":
                self._iteration,

            "ready":
                self.ready(),
        }



__all__ = [
    "DAGLoopIterationController",
]
