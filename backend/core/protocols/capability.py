from __future__ import annotations


from typing import Protocol, runtime_checkable



@runtime_checkable
class CapabilityProtocol(
    Protocol,
):
    """
    Component capability contract.


    Responsibility:

        - expose component capabilities


    Not Responsible:

        - capability execution
        - routing
        - permission
        - lifecycle
    """


    def capabilities(
        self,
    ) -> tuple[str, ...]:
        ...


__all__ = [
    "CapabilityProtocol",
]
