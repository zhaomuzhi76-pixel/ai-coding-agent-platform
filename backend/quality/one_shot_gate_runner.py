"""一次性门禁编排：跑完即出报告，不落盘、不退出终端。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from backend.quality.gate_contract import GateContext, GateResult
from backend.quality.gate_registry import GateRegistry


@dataclass
class OneShotReport:
    results: List[GateResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def summary(self) -> str:
        lines = ["=== OneShot Quality Gate ==="]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"[{status}] {r.name} metrics={dict(r.metrics)}")
            for v in r.violations:
                lines.append(
                    f"  - [{v.severity}] {v.code} {v.location} {v.message}"
                )
        lines.append(f"OVERALL: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


class OneShotGateRunner:
    def __init__(self, registry: GateRegistry, context: GateContext) -> None:
        self._registry = registry
        self._context = context

    def run(self, layers: Optional[List[str]] = None) -> OneShotReport:
        report = OneShotReport()
        if layers:
            gates = [g for layer in layers for g in self._registry.for_layer(layer)]
        else:
            gates = self._registry.all()
        for gate in gates:
            report.results.append(gate.run(self._context))
        return report
