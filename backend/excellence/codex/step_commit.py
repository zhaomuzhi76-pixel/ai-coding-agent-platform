"""Atomic step-commit planner (Codex: 小步提交、避免破坏已有结构).

与 ModificationTransaction 的区别：
    Transaction    -> 状态机 + 阶段推进
    StepCommitPlan -> 规划「一次提交多少文件、什么顺序、依赖如何」
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StepCommit:
    step_id: int
    files: List[str]
    description: str = ""
    depends_on: List[int] = field(default_factory=list)
    changes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "files": list(self.files),
            "description": self.description,
            "depends_on": list(self.depends_on),
            "change_count": len(self.changes),
        }


@dataclass
class StepCommitPlan:
    steps: List[StepCommit] = field(default_factory=list)
    strategy: str = "grouped_by_file"

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def file_count(self) -> int:
        return len({f for s in self.steps for f in s.files})

    def dump(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "step_count": self.step_count,
            "file_count": self.file_count,
            "steps": [s.to_dict() for s in self.steps],
        }


class StepCommitPlanner:
    """Group changes into ordered atomic commit steps."""

    VERSION = "1.0"

    def __init__(self, max_files_per_step: int = 3) -> None:
        if max_files_per_step <= 0:
            raise ValueError("max_files_per_step must positive")
        self._max = max_files_per_step

    def plan(
        self, changes: List[Dict[str, Any]],
    ) -> StepCommitPlan:
        if not changes:
            return StepCommitPlan(strategy="empty")
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for c in changes:
            if not isinstance(c, dict):
                continue
            f = str(c.get("file", "<unknown>"))
            by_file.setdefault(f, []).append(c)
        plan = StepCommitPlan(strategy="grouped_by_file")
        step_id = 1
        buffer: List[str] = []
        buffer_changes: List[Dict[str, Any]] = []
        for f, items in by_file.items():
            buffer.append(f)
            buffer_changes.extend(items)
            if len(buffer) >= self._max:
                plan.steps.append(StepCommit(
                    step_id=step_id,
                    files=list(buffer),
                    description=f"commit {len(buffer)} files",
                    depends_on=[step_id - 1] if step_id > 1 else [],
                    changes=list(buffer_changes),
                ))
                step_id += 1
                buffer = []
                buffer_changes = []
        if buffer:
            plan.steps.append(StepCommit(
                step_id=step_id,
                files=list(buffer),
                description=f"commit {len(buffer)} files",
                depends_on=[step_id - 1] if step_id > 1 else [],
                changes=list(buffer_changes),
            ))
        return plan

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "max_files_per_step": self._max,
        }


__all__ = ["StepCommit", "StepCommitPlan", "StepCommitPlanner"]
