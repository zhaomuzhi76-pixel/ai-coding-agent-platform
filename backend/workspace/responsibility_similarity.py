from __future__ import annotations

from typing import Any


class ResponsibilitySimilarity:
    """
    Responsibility similarity calculator.

    Responsibility:
        - calculate similarity between two responsibility profiles
        - evaluate responsibility overlap by weighted features

    Not Responsible:
        - extract responsibilities
        - scan workspace
        - detect conflicts
        - generate reports
    """

    VERSION = "3.0"

    RESPONSIBILITY = (
        "weighted_responsibility_similarity"
    )

    RESPONSIBILITY_WEIGHT = 0.4
    CLASS_WEIGHT = 0.3
    METHOD_WEIGHT = 0.2
    KEYWORD_WEIGHT = 0.1

    def calculate(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> float:

        responsibility_score = self._score(
            left.get("responsibilities", []),
            right.get("responsibilities", []),
        )

        if not responsibility_score:
            responsibility_score = self._score(
                [
                    left.get(
                        "responsibility",
                        "",
                    )
                ],
                [
                    right.get(
                        "responsibility",
                        "",
                    )
                ],
            )

        class_score = self._score(
            left.get("classes", []),
            right.get("classes", []),
        )

        if not class_score:
            class_score = self._score(
                left.get("names", []),
                right.get("names", []),
            )

        method_score = self._score(
            left.get("methods", []),
            right.get("methods", []),
        )

        keyword_score = self._score(
            left.get("keywords", []),
            right.get("keywords", []),
        )

        result = (
            responsibility_score
            * self.RESPONSIBILITY_WEIGHT
            +
            class_score
            * self.CLASS_WEIGHT
            +
            method_score
            * self.METHOD_WEIGHT
            +
            keyword_score
            * self.KEYWORD_WEIGHT
        )

        return round(
            result,
            3,
        )

    def _score(
        self,
        left: list[Any],
        right: list[Any],
    ) -> float:

        left_tokens = self._normalize(
            left
        )

        right_tokens = self._normalize(
            right
        )

        return self._jaccard(
            left_tokens,
            right_tokens,
        )

    def _normalize(
        self,
        values: list[Any],
    ) -> set[str]:

        result = set()

        for value in values:
            text = str(
                value
            ).strip().lower()

            if text:
                result.add(
                    text
                )

        return result

    def _jaccard(
        self,
        left: set[str],
        right: set[str],
    ) -> float:

        if not left and not right:
            return 0.0

        union = (
            left
            |
            right
        )

        if not union:
            return 0.0

        common = (
            left
            &
            right
        )

        return (
            len(common)
            /
            len(union)
        )

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "ResponsibilitySimilarity",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "ResponsibilitySimilarity",
]
