from __future__ import annotations

import subprocess
from typing import Any

class TestExecutor:
    """
    Verification command execution owner.

    Responsibility:
        - validate command contract
        - execute verification commands
        - normalize process results

    Not Responsible:
        - syntax checking
        - patch execution
        - rollback
        - result aggregation
    """

    VERSION = "2.0"
    RESPONSIBILITY = (
        "code_test_command_execution",
    )

    TIMEOUT = 120

    def execute(
        self,
        command: list[str],
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        if not self._valid_command(command):
            return {
                "success": False,
                "error": "invalid_command",
            }

        effective_timeout = (
            self.TIMEOUT
            if timeout is None
            else timeout
        )

        if effective_timeout <= 0:
            return {
                "success": False,
                "error": "invalid_timeout",
            }

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "error": "timeout",
                "detail": str(exc),
            }
        except Exception as exc:
            return {
                "success": False,
                "error": "execution_failed",
                "detail": str(exc),
            }

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "code": result.returncode,
            "command": list(command),
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "timeout": self.TIMEOUT,
        }

    @staticmethod
    def _valid_command(
        command: list[str],
    ) -> bool:
        return (
            isinstance(command, list)
            and bool(command)
            and all(
                isinstance(item, str)
                and bool(item.strip())
                for item in command
            )
        )

__all__ = [
    "TestExecutor",
]
