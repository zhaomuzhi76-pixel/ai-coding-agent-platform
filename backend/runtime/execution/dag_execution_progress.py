from __future__ import annotations


class DAGExecutionProgress:
    """
    DAG execution progress monitor.

    Responsibility:
        - detect execution progress
        - reject a stalled execution round

    Not Responsible:
        - execution
        - scheduling
        - state mutation
    """

    VERSION = "1.1"

    MAX_STALLED_ROUNDS = 1

    def __init__(
        self,
    ) -> None:
        self.stalled = 0

    def check(
        self,
        before,
        after,
    ) -> None:
        if before != after:
            self.stalled = 0
            return

        self.stalled += 1

        if self.stalled >= self.MAX_STALLED_ROUNDS:
            raise RuntimeError(
                "execution stalled: no state progress"
            )

    def reset(
        self,
    ) -> None:
        self.stalled = 0

    def ready(
        self,
    ) -> bool:
        return self.MAX_STALLED_ROUNDS > 0

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "max_stalled_rounds": (
                self.MAX_STALLED_ROUNDS
            ),
            "stalled": self.stalled,
            "ready": self.ready(),
        }


__all__ = [
    "DAGExecutionProgress",
]
