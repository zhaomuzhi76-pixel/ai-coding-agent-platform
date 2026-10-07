from __future__ import annotations

import re
from typing import Dict

from backend.agent.planner.task_category_rules import (
    TaskCategoryRules,
)


class TaskClassifier:
    VERSION = "5.4"

    RESPONSIBILITY = (
        "task_classification",
    )

    PRIORITY = (
        "code_analysis",
        "workspace_scan",
        "file_edit",
        "file_read",
        "file_write",
        "test",
        "deployment",
        "summary",
        "text_generate",
    )

    READ_ONLY_MARKERS = (
        "不要修改",
        "不修改",
        "无需修改",
        "不需要修改",
        "勿修改",
        "只读",
        "仅读",
        "don't modify",
        "do not modify",
        "without modifying",
        "read-only",
        "read only",
    )

    READ_MARKERS = (
        "读取",
        "读一下",
        "查看",
        "打开",
        "告诉我",
        "看看",
        "read",
        "open",
        "inspect",
    )

    def __init__(
        self,
        rules: TaskCategoryRules | None = None,
    ) -> None:
        self.rules = rules or TaskCategoryRules()

    def classify(
        self,
        message: str,
    ) -> str:
        if not isinstance(message, str) or not message.strip():
            return "general"

        text = message.lower()

        if self._is_read_only_request(text):
            return "file_read"

        if self._has_explicit_file_target(text):
            if self._contains_any(
                text,
                self.rules.CODE_ACTIONS,
            ):
                return "code_analysis"

        if self._match_special(
            text,
            self.rules.WORKSPACE_TARGETS,
            self.rules.WORKSPACE_ACTIONS,
        ):
            return "workspace_scan"

        for category in (
            "file_edit",
            "file_read",
            "file_write",
            "test",
            "deployment",
            "summary",
            "text_generate",
        ):
            if self._contains_any(
                text,
                self.rules.CATEGORY_RULES.get(
                    category,
                    (),
                ),
            ):
                return category

        return "general"

    def normalize(
        self,
        category: str,
    ) -> str:
        if not isinstance(category, str):
            raise TypeError("category must be str")
        return category.strip()

    def _is_read_only_request(
        self,
        text: str,
    ) -> bool:
        return (
            self._has_explicit_file_target(text)
            and self._contains_any(
                text,
                self.READ_MARKERS,
            )
            and self._contains_any(
                text,
                self.READ_ONLY_MARKERS,
            )
        )

    def _match_special(
        self,
        text: str,
        targets: tuple[str, ...],
        actions: tuple[str, ...],
    ) -> bool:
        return (
            self._contains_any(text, targets)
            and self._contains_any(text, actions)
        )

    def _has_explicit_file_target(
        self,
        text: str,
    ) -> bool:
        return any(
            extension in text
            for extension in self.rules.FILE_EXTENSIONS
        )

    def _contains_any(
        self,
        text: str,
        keywords: tuple[str, ...],
    ) -> bool:
        return any(
            self._keyword_matches(text, keyword)
            for keyword in keywords
        )

    @staticmethod
    def _keyword_matches(
        text: str,
        keyword: str,
    ) -> bool:
        normalized = keyword.lower().strip()

        if not normalized:
            return False

        if normalized.isascii():
            pattern = (
                r"(?<![a-z0-9_])"
                + re.escape(normalized)
                + r"(?![a-z0-9_])"
            )
            return re.search(pattern, text) is not None

        return normalized in text

    def ready(self) -> bool:
        return bool(
            self.rules
            and self.rules.CATEGORY_RULES
        )

    def dump(
        self,
    ) -> Dict[str, object]:
        return {
            "name": "TaskClassifier",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "priority": list(self.PRIORITY),
            "category_aliases": dict(
                getattr(
                    self.rules,
                    "CATEGORY_ALIASES",
                    {},
                )
            ),
        }


__all__ = [
    "TaskClassifier",
]
