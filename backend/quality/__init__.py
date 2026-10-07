"""Quality 层：工业级门禁与一次性内存测试。只依赖标准库。"""
from backend.quality.gate_contract import Gate, GateContext, GateResult, GateViolation
from backend.quality.gate_registry import GateRegistry
from backend.quality.in_memory_test_runner import InMemoryTestRunner, TestCase, TestReport
from backend.quality.layer_dependency_gate import LayerDependencyGate
from backend.quality.line_limit_gate import LineLimitGate
from backend.quality.one_shot_gate_runner import OneShotGateRunner, OneShotReport

__all__ = [
    "Gate", "GateContext", "GateResult", "GateViolation",
    "GateRegistry", "InMemoryTestRunner", "TestCase", "TestReport",
    "LayerDependencyGate", "LineLimitGate",
    "OneShotGateRunner", "OneShotReport",
]
