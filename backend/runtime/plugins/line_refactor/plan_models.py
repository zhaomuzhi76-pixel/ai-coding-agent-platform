"""行数重构计划数据模型。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class PartSpec:
    filename: str
    source: str
    exported_names: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SplitPlan:
    source_path: str
    package_dir: str
    original_lines: int
    init_source: str
    parts: List[PartSpec] = field(default_factory=list)
    skipped_reason: str = ""

    @property
    def applicable(self) -> bool:
        return bool(self.parts) and not self.skipped_reason


@dataclass(frozen=True)
class RefactorPlan:
    splits: List[SplitPlan] = field(default_factory=list)
    hard_limit: int = 230
    soft_limit: int = 180

    @property
    def applicable(self) -> List[SplitPlan]:
        return [s for s in self.splits if s.applicable]

    @property
    def skipped(self) -> List[SplitPlan]:
        return [s for s in self.splits if not s.applicable]

    def summary(self) -> str:
        lines = ["=== Line Refactor Plan ==="]
        lines.append(
            f"total={len(self.splits)} "
            f"applicable={len(self.applicable)} "
            f"skipped={len(self.skipped)}"
        )
        for s in self.splits:
            if s.applicable:
                lines.append(
                    f"[SPLIT] {s.source_path} ({s.original_lines} lines) "
                    f"-> {len(s.parts)} parts"
                )
            else:
                lines.append(
                    f"[SKIP]  {s.source_path} ({s.original_lines} lines) "
                    f"reason={s.skipped_reason}"
                )
        return "\n".join(lines)


@dataclass
class ApplyReport:
    written: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["=== Line Refactor Apply ==="]
        for p in self.written:
            lines.append(f"[WRITE]  {p}")
        for p in self.removed:
            lines.append(f"[REMOVE] {p}")
        for p in self.failed:
            lines.append(f"[FAIL]   {p}")
        return "\n".join(lines)
