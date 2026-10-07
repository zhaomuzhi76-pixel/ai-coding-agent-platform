"""
=========================================================

Prompt Renderer

Responsibility:

    - Render prompt variables
    - Replace {{variable}} placeholders

Not responsible:

    - Load prompt
    - Register prompt
    - Cache prompt
    - Execute prompt

=========================================================
"""

from __future__ import annotations

import re
from typing import Any


_VARIABLE_PATTERN = re.compile(
    r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}"
)


class PromptRenderer:
    """
    Render prompt variables.
    """

    def render(
        self,
        template: str,
        **kwargs: Any,
    ) -> str:
        """
        Render template.
        """

        if not template:
            return ""

        def replace(match):
            key = match.group(1)

            value = kwargs.get(
                key,
                "",
            )

            if value is None:
                return ""

            return str(value)

        return _VARIABLE_PATTERN.sub(
            replace,
            template,
        )


__all__ = [
    "PromptRenderer",
]
