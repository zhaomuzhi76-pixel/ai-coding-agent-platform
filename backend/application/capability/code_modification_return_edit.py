from __future__ import annotations

import re


class CodeModificationReturnEdit:
    """
    Deterministic resolver for explicit function-return edits.

    Responsibility:
        - recognize an explicit return-value change
        - produce one exact source replacement candidate

    Safety:
        - never return a no-op edit
        - old text must exist verbatim in source
        - old and new text must differ
        - ambiguous natural language falls back to LLM proposal
    """

    VERSION = "3.0"

    _PATTERNS = (
        re.compile(
            r"(?is)"
            r"\b(?:change|modify|edit|update)\b"
            r".*?\breturn\b\s+(.+?)"
            r"\s+(?:to|into|as)\s+"
            r"(?:return\b\s*)?(.+?)"
            r"(?:[.!?]|$)"
        ),
        re.compile(
            r"(?is)"
            r"\breturn\b\s+(.+?)"
            r"\s*(?:->|=>|to)\s*"
            r"(?:return\b\s*)?(.+?)"
            r"(?:[.!?]|$)"
        ),
        re.compile(
            r"(?is)"
            r"\breturn\s+(.+?)\s+"
            r"(?:改为|修改为|变为|替换为)\s+"
            r"(?:return\s+)?(.+?)(?:[。！？]|$)"
        ),
    )

    def resolve(
        self,
        *,
        task: str,
        source: str,
    ) -> dict[str, str] | None:
        self._validate(task, source)

        for pattern in self._PATTERNS:
            match = pattern.search(task)
            if match is None:
                continue

            candidate = self._candidate(
                source,
                match.group(1),
                match.group(2),
            )

            if candidate is not None:
                return candidate

        return None

    @classmethod
    def _candidate(
        cls,
        source: str,
        old_value: str,
        new_value: str,
    ) -> dict[str, str] | None:
        old_value = cls._clean(old_value)
        new_value = cls._clean(new_value)

        if not old_value or not new_value:
            return None

        old_lines = cls._return_lines(
            source,
            old_value,
        )

        if len(old_lines) != 1:
            return None

        old_line = old_lines[0]
        new_line = cls._replace_return_value(
            old_line,
            old_value,
            new_value,
        )

        if new_line is None:
            return None

        if new_line == old_line:
            return None

        if new_line not in source.replace(
            old_line,
            "",
            1,
        ):
            replacement = source.replace(
                old_line,
                new_line,
                1,
            )
        else:
            replacement = source.replace(
                old_line,
                new_line,
                1,
            )

        if replacement == source:
            return None

        return {
            "old": old_line,
            "new": new_line,
            "strategy": "explicit_return",
        }

    @staticmethod
    def _return_lines(
        source: str,
        value: str,
    ) -> list[str]:
        result: list[str] = []

        for line in source.splitlines(keepends=True):
            stripped = line.strip()
            if not stripped.startswith("return"):
                continue

            expression = stripped[
                len("return"):
            ].strip()

            if expression == value:
                result.append(line)

        return result

    @staticmethod
    def _replace_return_value(
        line: str,
        old_value: str,
        new_value: str,
    ) -> str | None:
        match = re.match(
            r"^(?P<indent>\s*)return\b(?P<body>.*?)(?P<newline>\r?\n)?$",
            line,
            re.IGNORECASE,
        )

        if match is None:
            return None

        body = match.group("body").strip()
        if body != old_value:
            return None

        newline = match.group("newline") or ""
        return (
            f"{match.group('indent')}return {new_value}"
            f"{newline}"
        )

    @staticmethod
    def _clean(value: object) -> str:
        if not isinstance(value, str):
            return ""

        value = value.strip()

        if value.lower().startswith("return "):
            value = value[7:].strip()

        return value.rstrip(
            ".。!?！？"
        ).strip()

    @staticmethod
    def _validate(
        task: str,
        source: str,
    ) -> None:
        if not isinstance(task, str) or not task.strip():
            raise ValueError(
                "return edit task required"
            )

        if not isinstance(source, str):
            raise TypeError(
                "return edit source must str"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "patterns": len(self._PATTERNS),
        }


__all__ = [
    "CodeModificationReturnEdit",
]
