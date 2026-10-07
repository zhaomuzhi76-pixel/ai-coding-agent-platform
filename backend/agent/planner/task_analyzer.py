from __future__ import annotations

from typing import Any

from backend.agent.planner.task_analysis import (
    TaskAnalysis,
)

from backend.agent.planner.task_classifier import (
    TaskClassifier,
)

from backend.agent.planner.complexity_estimator import (
    ComplexityEstimator,
)

from backend.agent.planner.capability_detector import (
    CapabilityDetector,
)

from backend.agent.planner.risk_assessor import (
    RiskAssessor,
)


class TaskAnalyzer:
    """
    Task analysis facade.

    Responsibility:

        - coordinate analysis components
        - aggregate task analysis result

    Not Responsible:

        - classification rules
        - complexity rules
        - capability rules
        - risk rules
        - parameter extraction
        - planning
        - execution
    """

    VERSION = "5.0"

    RESPONSIBILITY = (
        "task_analysis_facade"
    )

    def __init__(
        self,
        classifier: TaskClassifier | None = None,
        complexity_estimator: ComplexityEstimator | None = None,
        capability_detector: CapabilityDetector | None = None,
        risk_assessor: RiskAssessor | None = None,
    ) -> None:

        self.classifier = (
            classifier
            or TaskClassifier()
        )

        self.complexity_estimator = (
            complexity_estimator
            or ComplexityEstimator()
        )

        self.capability_detector = (
            capability_detector
            or CapabilityDetector()
        )

        self.risk_assessor = (
            risk_assessor
            or RiskAssessor()
        )

    def analyze(
        self,
        message: str,
    ) -> TaskAnalysis:

        return TaskAnalysis.from_message(
            task_type=(
                self.classifier.classify(
                    message
                )
            ),

            complexity=(
                self.complexity_estimator.estimate(
                    message
                )
            ),

            required_capabilities=(
                self.capability_detector.detect(
                    message
                )
            ),

            risk_level=(
                self.risk_assessor.assess(
                    message
                )
            ),

            message=message,
        )

    def ready(
        self,
    ) -> bool:

        return all(
            (
                self.classifier,
                self.complexity_estimator,
                self.capability_detector,
                self.risk_assessor,
            )
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "TaskAnalyzer",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "classifier":
                self.classifier.dump(),

            "complexity":
                self.complexity_estimator.dump(),

            "capability":
                self.capability_detector.dump(),

            "risk":
                self.risk_assessor.dump(),
        }


__all__ = [
    "TaskAnalyzer",
]
