from __future__ import annotations



class DAGExecutionStream:
    """
    DAG execution output stream.


    Responsibility:
        - forward execution events


    Not Responsible:
        - execution
        - state
        - scheduling
    """


    VERSION = "1.0"



    async def emit(
        self,
        callback,
        batch,
    ) -> None:


        if callback is None:
            return


        for item in batch:
            await callback(
                item
            )



    def ready(
        self,
    ) -> bool:

        return True



__all__ = [
    "DAGExecutionStream",
]
