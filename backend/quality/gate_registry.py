"""门禁注册表。按层注册，禁止跨层乱注册。"""
from __future__ import annotations

from typing import Dict, Iterable, List

from backend.quality.gate_contract import Gate


class GateRegistry:
    def __init__(self) -> None:
        self._by_layer: Dict[str, List[Gate]] = {}

    def register(self, gate: Gate) -> None:
        self._by_layer.setdefault(gate.layer, []).append(gate)

    def register_all(self, gates: Iterable[Gate]) -> None:
        for gate in gates:
            self.register(gate)

    def layers(self) -> List[str]:
        return sorted(self._by_layer.keys())

    def for_layer(self, layer: str) -> List[Gate]:
        return list(self._by_layer.get(layer, ()))

    def all(self) -> List[Gate]:
        result: List[Gate] = []
        for layer in self.layers():
            result.extend(self._by_layer[layer])
        return result


# auto-appended by one-shot fixer
GATES: tuple = ()
