from __future__ import annotations

import re

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class TaskAnalysis:
    """
    Task analysis result model.

    Responsibility:

        - store task analysis result
        - normalize task parameters
        - serialize analysis data

    Owns:

        - task_type
        - complexity
        - required_capabilities
        - risk_level
        - parameters

    Not Responsible:

        - task classification
        - complexity estimation
        - capability detection
        - risk assessment
        - planning
        - execution
    """

    VERSION = "3.1"

    RESPONSIBILITY = (
        "task_analysis_model"
    )

    task_type: str

    complexity: str

    required_capabilities: List[str]

    risk_level: str = "low"

    parameters: Dict[str, Any] = field(
        default_factory=dict
    )

    @classmethod
    def from_message(
        cls,
        task_type: str,
        complexity: str,
        required_capabilities: List[str],
        risk_level: str,
        message: str,
    ) -> "TaskAnalysis":

        return cls(
            task_type=task_type,
            complexity=complexity,
            required_capabilities=required_capabilities,
            risk_level=risk_level,
            parameters=cls.extract_parameters(
                message
            ),
        )

    @staticmethod
    def extract_parameters(
        message: str,
    ) -> Dict[str, Any]:

        parameters: Dict[str, Any] = {}

        if not message:
            return parameters

        pattern = (
            r"([A-Za-z0-9_][A-Za-z0-9_./\\-]*\."
            r"(?:py|txt|md|json|yaml|yml|js|ts))"
        )

        match = re.search(
            pattern,
            message,
        )

        if match:
            parameters["path"] = (
                match.group(1)
            )

        return parameters

    def ready(
        self,
    ) -> bool:

        return bool(
            self.task_type
            and self.complexity
        )

    def dump(
        self,
    ) -> Dict[str, Any]:

        return {
            "name":
                "TaskAnalysis",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "task_type":
                self.task_type,

            "complexity":
                self.complexity,

            "required_capabilities":
                self.required_capabilities,

            "risk_level":
                self.risk_level,

            "parameters":
                self.parameters,
        }


__all__ = [
    "TaskAnalysis",
]
