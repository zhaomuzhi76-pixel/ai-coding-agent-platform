"""召回参数配置单例（L0 · 无依赖）—— 面板"应用"后主检索立即读到。"""
from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class RecallConfig:
    top_k: int = 10
    use_reranker: bool = True
    reranker_model_id: str = "builtin-qwen3-reranker"
    rrf_k: int = 60
    vector_weight: float = 0.7
    bm25_weight: float = 0.3

    def to_dict(self) -> dict:
        return asdict(self)


class RecallConfigStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cfg = RecallConfig()
        self._version = 0

    def get(self) -> RecallConfig:
        with self._lock:
            return self._cfg

    def version(self) -> int:
        with self._lock:
            return self._version

    def apply(self, **changes) -> RecallConfig:
        with self._lock:
            allowed = {f: changes[f] for f in changes
                       if f in RecallConfig.__dataclass_fields__}
            self._cfg = replace(self._cfg, **allowed)
            self._version += 1
            return self._cfg

    def reset(self) -> RecallConfig:
        with self._lock:
            self._cfg = RecallConfig()
            self._version += 1
            return self._cfg


_default: RecallConfigStore | None = None
_lock = threading.Lock()


def get_default_config() -> RecallConfigStore:
    global _default
    with _lock:
        if _default is None:
            _default = RecallConfigStore()
        return _default
