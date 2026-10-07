"""EvolutionTracker: 长期演进的趋势检测 (Claude Code: 长期演进能力).

与 RepairHistory 的区别：
    RepairHistory -> 事件列表
    EvolutionTracker -> 趋势线（行数、文件数、包数随时间的走向）
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.excellence.claude.repo_map import RepoMap


@dataclass
class EvolutionSnapshot:
    total_files: int
    total_lines: int
    total_packages: int
    created_at: float = field(default_factory=time.time)
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "total_packages": self.total_packages,
            "created_at": self.created_at,
            "label": self.label,
        }

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class TrendPoint:
    metric: str
    delta: float
    pct_change: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "delta": self.delta,
            "pct_change": round(self.pct_change, 4),
        }


class EvolutionTracker:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._snapshots: List[EvolutionSnapshot] = []

    def capture(self, repo_map: RepoMap, label: str = "") -> EvolutionSnapshot:
        snap = EvolutionSnapshot(
            total_files=repo_map.total_files,
            total_lines=repo_map.total_lines,
            total_packages=len(repo_map.packages),
            label=label,
        )
        self._snapshots.append(snap)
        return snap

    def snapshots(self) -> List[EvolutionSnapshot]:
        return list(self._snapshots)

    def trends(self, since: Optional[int] = None) -> List[TrendPoint]:
        snaps = self._snapshots[since:] if since is not None else self._snapshots
        if len(snaps) < 2:
            return []
        first, last = snaps[0], snaps[-1]
        out: List[TrendPoint] = []
        for name, a, b in (
            ("files", first.total_files, last.total_files),
            ("lines", first.total_lines, last.total_lines),
            ("packages", first.total_packages, last.total_packages),
        ):
            delta = float(b - a)
            pct = (delta / a) if a else 0.0
            out.append(TrendPoint(metric=name, delta=delta,
                                  pct_change=pct))
        return out

    def summary(self) -> Dict[str, Any]:
        return {
            "snapshots": len(self._snapshots),
            "trends": [t.to_dict() for t in self.trends()],
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "snapshots": len(self._snapshots),
        }


__all__ = ["EvolutionSnapshot", "TrendPoint", "EvolutionTracker"]
