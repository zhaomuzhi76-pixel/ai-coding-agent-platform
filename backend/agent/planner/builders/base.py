"""
Planner Step Builder Base

Responsibility:

    - define common builder interface

Owns:

    - builder contract
    - builder metadata

Not Responsible:

    - intent detection
    - task parsing
    - workflow composition
    - execution
"""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)

from typing import (
    Any,
    Dict,
    List,
)

from backend.agent.planner.models.plan_step import (
    PlanStep,
)


class BaseStepBuilder(
    ABC,
):
    """
    Base interface for planner step builders.
    """

    VERSION = "2.0"


    def ready(
        self,
    ) -> bool:

        return True


    @abstractmethod
    def build(
        self,
        context: Dict[str, Any] | None = None,
    ) -> List[PlanStep]:
        """
        Create planner steps.
        """

        raise NotImplementedError


    def dump(
        self,
    ) -> Dict[str, Any]:

        return {

            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "responsibility":
                "planner_step_builder",

            "ready":
                self.ready(),

        }


__all__ = [
    "BaseStepBuilder",
]
