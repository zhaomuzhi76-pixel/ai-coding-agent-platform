from __future__ import annotations


from typing import Protocol, runtime_checkable



@runtime_checkable
class RuntimeStateProtocol(
    Protocol,
):
    """
    Runtime state contract.


    Responsibility:

        - expose runtime lifecycle state


    Not Responsible:

        - state transition logic
        - persistence
        - execution scheduling
    """



    @property
    def state(
        self,
    ) -> str:
        ...



    def is_terminal(
        self,
    ) -> bool:
        ...



__all__ = [
    "RuntimeStateProtocol",
]
