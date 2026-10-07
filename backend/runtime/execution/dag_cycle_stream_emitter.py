from __future__ import annotations


from backend.runtime.execution.dag_execution_stream import (
    DAGExecutionStream,
)


class DAGCycleStreamEmitter:
    """
    DAG cycle stream emission boundary.

    Responsibility:
        - emit cycle outputs

    Not Responsible:
        - execution
        - scheduling
        - state mutation
        - progress detection
    """


    VERSION = "1.0"



    def __init__(
        self,
        stream: DAGExecutionStream,
    ) -> None:

        if stream is None:
            raise ValueError(
                "stream required"
            )

        self.stream = stream



    async def emit(
        self,
        callback,
        outputs,
    ) -> None:

        await self.stream.emit(
            callback,
            outputs,
        )



    def ready(
        self,
    ) -> bool:

        return self.stream.ready()



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name":
                "DAGCycleStreamEmitter",

            "version":
                self.VERSION,

            "ready":
                self.ready(),
        }



__all__ = [
    "DAGCycleStreamEmitter",
]
