from __future__ import annotations

from pathlib import Path
from typing import Any

class VerificationRunner:
    """
    Verification workflow coordinator.

    Responsibility:
        - coordinate syntax and command verification
        - aggregate verification results
        - normalize verification stages

    Not Responsible:
        - syntax implementation
        - command execution implementation
        - patch execution
        - rollback
        - repair
    """

    VERSION = "7.0"
    RESPONSIBILITY = (
        "industrial_verification_coordination",
    )

    def __init__(
        self,
        syntax_checker: Any,
        test_executor: Any,
    ) -> None:
        if syntax_checker is None:
            raise ValueError(
                "syntax_checker required"
            )

        if test_executor is None:
            raise ValueError(
                "test_executor required"
            )

        self.syntax_checker = syntax_checker
        self.test_executor = test_executor
        self.verify_count = 0
        self.success_count = 0
        self.failure_count = 0

    def verify(
        self,
        file: str,
        *,
        root: str | None = None,
        command: list[str] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        self.verify_count += 1

        if not self.ready():
            return self._failed(
                "dependency_missing"
            )

        path = (
            Path(root) / file
            if root
            and not Path(file).is_absolute()
            else Path(file)
        )

        target = str(path)

        syntax = self.syntax_checker.check(target)

        if not syntax.get("success", False):
            return self._failed(
                "syntax",
                result=syntax,
                file=file,
            )

        if command is None:
            self.success_count += 1
            return {
                "success": True,
                "stage": "syntax",
                "file": file,
                "syntax": syntax,
            }

        test = self.test_executor.execute(
            command,
            timeout=timeout,
        )

        if not test.get("success", False):
            return self._failed(
                "test",
                result=test,
                file=file,
            )

        self.success_count += 1

        return {
            "success": True,
            "stage": "completed",
            "file": file,
            "syntax": syntax,
            "test": test,
        }

    def verify_batch(
        self,
        files: list[str],
        *,
        command: list[str] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        if not isinstance(files, list):
            return {
                "success": False,
                "results": [],
                "failed_files": [],
                "error": "invalid_files",
            }

        results = [
            self.verify(
                file=item,
                command=command,
                timeout=timeout,
            )
            for item in files
        ]

        failed = [
            item.get("file")
            for item in results
            if not item.get("success", False)
        ]

        return {
            "success": not failed,
            "results": results,
            "failed_files": failed,
        }

    def ready(self) -> bool:
        return (
            self.syntax_checker is not None
            and self.test_executor is not None
            and callable(self.syntax_checker.check)
            and callable(self.test_executor.execute)
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "components": {
                "syntax_checker": type(
                    self.syntax_checker
                ).__name__,
                "test_executor": type(
                    self.test_executor
                ).__name__,
            },
            "metrics": {
                "verify": self.verify_count,
                "success": self.success_count,
                "failure": self.failure_count,
            },
            "capabilities": [
                "syntax_verification",
                "test_verification",
                "batch_verification",
            ],
        }

    def _failed(
        self,
        stage: str,
        **data: Any,
    ) -> dict[str, Any]:
        self.failure_count += 1
        return {
            "success": False,
            "stage": stage,
            **data,
        }

__all__ = [
    "VerificationRunner",
]
