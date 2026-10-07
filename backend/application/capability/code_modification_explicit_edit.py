from __future__ import annotations

import re


class CodeModificationExplicitEdit:
    """
    Resolve explicit variable value replacements.

    Example:
        把 VALUE 从 'BEFORE' 改成 'AFTER'

    Produces exact source fragments:
        old = "VALUE = 'BEFORE'"
        new = "VALUE = 'AFTER'"
    """

    VERSION = "1.2"

    _PATTERN = re.compile(
        r"(?:把|将)\s*"
        r"([A-Za-z_]\w*)\s*"
        r"从\s*"
        r"(['\"])(.*?)\2\s*"
        r"(?:改成|修改为|替换为)\s*"
        r"(['\"])(.*?)\4",
        re.DOTALL,
    )

    def resolve(
        self,
        *,
        task: str,
        source: str,
    ) -> dict[str, str] | None:
        if not isinstance(task, str) or not task.strip():
            return None
        if not isinstance(source, str):
            raise TypeError("source must str")

        match = self._PATTERN.search(task)
        if match is None:
            return None

        name = match.group(1)
        old_value = match.group(3)
        new_value = match.group(5)

        old = f"{name} = {match.group(2)}{old_value}{match.group(2)}"
        new = f"{name} = {match.group(4)}{new_value}{match.group(4)}"

        if old == new:
            raise ValueError("explicit edit is a no-op")

        if source.count(old) != 1:
            raise ValueError(
                "explicit old text must occur exactly once"
            )

        return {
            "old": old,
            "new": new,
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "CodeModificationExplicitEdit",
]
