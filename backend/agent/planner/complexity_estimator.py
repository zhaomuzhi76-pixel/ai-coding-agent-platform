from __future__ import annotations

from typing import Any


class ComplexityEstimator:
    """
    Task complexity estimator.

    Responsibility:

        - evaluate task complexity
        - provide complexity evidence

    Not Responsible:

        - task classification
        - capability detection
        - risk assessment
        - planning
        - execution
    """

    VERSION = "2.0"

    RESPONSIBILITY = "complexity_estimation"

    LEVEL_SIMPLE = "simple"
    LEVEL_MEDIUM = "medium"
    LEVEL_COMPLEX = "complex"

    COMPLEXITY_RULES = {
        "architecture": (
            "系统",
            "架构",
            "重构",
            "多个文件",
            "模块",
            "整体",
        ),
        "automation": (
            "完整",
            "全部",
            "自动",
            "流程",
            "pipeline",
            "自动化",
        ),
        "scale": (
            "大规模",
            "批量",
            "全项目",
            "所有文件",
            "整个项目",
        ),
    }

    def estimate(
        self,
        message: str,
    ) -> str:

        return self.estimate_detail(
            message
        )["level"]

    def estimate_detail(
        self,
        message: str,
    ) -> dict[str, Any]:

        text = (
            message.lower()
            if message
            else ""
        )

        matched = []
        score = 0

        for category, keywords in self.COMPLEXITY_RULES.items():

            hits = [
                keyword
                for keyword in keywords
                if keyword.lower() in text
            ]

            if not hits:
                continue

            score += len(hits)

            matched.append(
                {
                    "category": category,
                    "keywords": hits,
                }
            )

        level = self._resolve_level(
            score
        )

        return {
            "level": level,
            "score": score,
            "matched": matched,
        }

    def _resolve_level(
        self,
        score: int,
    ) -> str:

        if score >= 4:
            return self.LEVEL_COMPLEX

        if score >= 1:
            return self.LEVEL_MEDIUM

        return self.LEVEL_SIMPLE

    def ready(
        self,
    ) -> bool:

        return bool(
            self.COMPLEXITY_RULES
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "ComplexityEstimator",
            "version":
                self.VERSION,
            "responsibility":
                self.RESPONSIBILITY,
            "ready":
                self.ready(),
            "rule_groups":
                len(
                    self.COMPLEXITY_RULES
                ),
        }


__all__ = [
    "ComplexityEstimator",
]
