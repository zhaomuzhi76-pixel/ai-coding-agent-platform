from __future__ import annotations


class DAGIterationPolicy:
    """
    DAG iteration limit policy.


    Responsibility:
        - control iteration limit


    Not Responsible:
        - execution
        - scheduling
        - state
    """


    VERSION = "1.0"


    def __init__(
        self,
        max_iterations: int = 1000,
    ) -> None:

        if max_iterations <= 0:
            raise ValueError(
                "max_iterations must positive"
            )

        self.max_iterations = max_iterations



    def validate(
        self,
        iteration: int,
    ) -> None:

        if iteration > self.max_iterations:
            raise RuntimeError(
                "execution iteration exceeded"
            )



    def ready(
        self,
    ) -> bool:

        return True



__all__ = [
    "DAGIterationPolicy",
]
