from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4
import os

from backend.code_intelligence.modification_workflow import (
    ModificationWorkflow,
)


class ModificationPipeline:
    """Code modification pipeline coordinator."""

    VERSION = "5.1"
    RESPONSIBILITY = "industrial_modification_pipeline_coordinator"

    def __init__(self, workflow: ModificationWorkflow) -> None:
        if workflow is None:
            raise ValueError("ModificationWorkflow required")
        self.workflow = workflow
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0

    def execute(
        self,
        *,
        task: str,
        files: list[str],
        context: dict[str, Any] | None = None,
        root: str | None = None,
    ) -> dict[str, Any]:
        self._validate_input(task, files)
        runtime = dict(context or {})
        runtime["files"] = list(files)
        runtime["root"] = self._resolve_root(root, runtime, files)
        self._ensure_changes(runtime, task, files)

        self.execution_count += 1
        request_id = str(uuid4())
        try:
            result = self.workflow.execute(
                task=task,
                files=files,
                context=runtime,
            )
            if not isinstance(result, dict):
                raise TypeError("modification workflow result must dict")
            success = bool(result.get("success", False))
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
            return {
                "request_id": request_id,
                "pipeline": self.RESPONSIBILITY,
                "success": success,
                "result": result,
            }
        except Exception:
            self.failure_count += 1
            raise

    @staticmethod
    def _validate_input(task: str, files: list[str]) -> None:
        if not isinstance(task, str) or not task.strip():
            raise ValueError("modification task required")
        if not isinstance(files, list) or not files:
            raise ValueError("modification files required")
        if any(not isinstance(file, str) or not file.strip() for file in files):
            raise ValueError("modification file paths required")

    @staticmethod
    def _resolve_root(
        root: str | None,
        runtime: dict[str, Any],
        files: list[str],
    ) -> str:
        value = root or runtime.get("root")
        if value is None:
            resolved = [
                Path(file).expanduser().resolve()
                for file in files
            ]
            parents = [
                str(file.parent if file.suffix else file)
                for file in resolved
            ]
            value = parents[0] if len(parents) == 1 else os.path.commonpath(parents)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("modification root required")
        return str(Path(value).expanduser().resolve())

    @staticmethod
    def _ensure_changes(
        runtime: dict[str, Any],
        task: str,
        files: list[str],
    ) -> None:
        changes = runtime.get("changes")
        if isinstance(changes, dict) and changes:
            return

        if len(files) != 1:
            raise ValueError(
                "modification changes required for multiple files"
            )

        source = runtime.get("source")
        if not isinstance(source, str):
            raise ValueError("modification source content required")

        instruction = runtime.get("instruction", task)
        runtime["changes"] = {
            files[0]: {
                "content": source,
                "instruction": (
                    instruction if isinstance(instruction, str) else task
                ),
            }
        }

    def ready(self) -> bool:
        return self.workflow.ready()

    def health(self) -> dict[str, Any]:
        return {
            "service": "ModificationPipeline",
            "status": "healthy" if self.ready() else "unhealthy",
            "version": self.VERSION,
        }

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "workflow": type(self.workflow).__name__,
            "metrics": {
                "execution": self.execution_count,
                "success": self.success_count,
                "failure": self.failure_count,
            },
            "capabilities": [
                "request_coordination",
                "context_normalization",
                "workflow_dispatch",
            ],
        }


__all__ = [
    "ModificationPipeline",
]
