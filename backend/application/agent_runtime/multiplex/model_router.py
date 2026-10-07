"""MultiplexModelRouter: 模型链解析（不依赖 role 抽象）。

契约：
  - route(chain) → (provider, model)：返回链中第一个"可用"的
  - 链 = ((provider, model), ...)；provider 可为 ""
  - is_available 谓词外部注入（默认全可用）
  - 全部不可用 → ModelResolveError

不负责：
  - 健康检查的具体实现（外部注入谓词）
  - 进程 / 调用
"""
from __future__ import annotations

from typing import Callable


class ModelResolveError(RuntimeError):
    """无可用模型。"""


class MultiplexModelRouter:
    VERSION = "1.0"

    def __init__(
        self,
        is_available: Callable[[str, str], bool] | None = None,
    ) -> None:
        self.is_available = is_available or (lambda p, m: True)
        self.resolved = 0
        self.fallback_used = 0

    def route(self, chain) -> tuple[str, str]:
        chain = tuple(chain or ())
        if not chain:
            raise ModelResolveError("empty model chain")
        for i, item in enumerate(chain):
            if isinstance(item, (tuple, list)) and len(item) == 2:
                provider, model = str(item[0]), str(item[1])
            elif isinstance(item, str):
                provider, model = "", item
            else:
                continue
            if not model.strip():
                continue
            if self.is_available(provider, model):
                self.resolved += 1
                if i > 0: self.fallback_used += 1
                return provider, model
        raise ModelResolveError(
            "no available model in chain (" + str(len(chain)) + ")"
        )

    def dump(self) -> dict:
        return {
            "name": type(self).__name__, "version": self.VERSION,
            "resolved": self.resolved, "fallback_used": self.fallback_used,
        }


__all__ = ["MultiplexModelRouter", "ModelResolveError"]
