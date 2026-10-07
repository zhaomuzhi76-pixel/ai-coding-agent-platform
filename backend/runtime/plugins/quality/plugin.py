"""Quality 插件入口：只接线，不重复实现门禁。"""
from __future__ import annotations

from backend.quality.gate_contract import GateContext
from backend.quality.gate_registry import GateRegistry
from backend.quality.layer_dependency_gate import LayerDependencyGate
from backend.quality.line_limit_gate import LineLimitGate
from backend.quality.one_shot_gate_runner import OneShotGateRunner


class QualityPlugin:
    name = "quality"
    version = "1.0.0"

    def build_registry(self) -> GateRegistry:
        registry = GateRegistry()
        registry.register_all([LineLimitGate(), LayerDependencyGate()])
        return registry

    def run_once(self, root: str) -> str:
        ctx = GateContext(root=root)
        return OneShotGateRunner(self.build_registry(), ctx).run().summary()
