from __future__ import annotations

import py_compile
from pathlib import Path
from typing import Any

class SyntaxChecker:
    """
    Python syntax verification owner.

    Responsibility:
        - validate Python source syntax

    Not Responsible:
        - test command execution
        - patch execution
        - repair
    """

    VERSION = "1.1"
    RESPONSIBILITY = (
        "code_syntax_validation",
    )

    def check(
        self,
        file: str,
    ) -> dict[str, Any]:
        if not file:
            return {
                "success": False,
                "error": "missing_file",
            }

        path = Path(file)

        if not path.exists():
            return {
                "success": False,
                "error": "file_not_found",
                "file": file,
            }

        if not path.is_file():
            return {
                "success": False,
                "error": "not_a_file",
                "file": file,
            }

        try:
            py_compile.compile(
                str(path),
                doraise=True,
            )
        except Exception as exc:
            return {
                "success": False,
                "error": "syntax_error",
                "detail": str(exc),
                "file": file,
            }

        return {
            "success": True,
            "file": file,
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }

__all__ = [
    "SyntaxChecker",
]
