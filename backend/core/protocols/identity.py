from __future__ import annotations


from typing import Protocol, runtime_checkable



@runtime_checkable
class IdentityProtocol(
    Protocol,
):
    """
    Component identity contract.


    Responsibility:

        - expose stable component identity


    Not Responsible:

        - lifecycle
        - health
        - metadata storage
        - execution
    """


    @property
    def component_id(
        self,
    ) -> str:
        ...


    @property
    def name(
        self,
    ) -> str:
        ...


    @property
    def component_type(
        self,
    ) -> str:
        ...


__all__ = [
    "IdentityProtocol",
]
