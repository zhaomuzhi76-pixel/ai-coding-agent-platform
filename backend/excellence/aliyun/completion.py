"""Aliyun-style code completion engine (阿里云: 代码补全).

输入：光标上下文（prefix + suffix + 语言 + 预算）
输出：completion candidates（排序后）
复用：ContextSelector 做预算裁剪；不重造 LLM 层，只做候选管理。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class CompletionContext:
    prefix: str
    suffix: str = ""
    language: str = "python"
    file_path: str = ""
    max_candidates: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prefix": self.prefix[-500:],
            "suffix": self.suffix[:500],
            "language": self.language,
            "file_path": self.file_path,
            "max_candidates": self.max_candidates,
        }


@dataclass
class Completion:
    text: str
    score: float = 0.0
    source: str = ""
    kind: str = "line"  # line | block | snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "score": round(self.score, 3),
            "source": self.source,
            "kind": self.kind,
        }


class CompletionEngine:
    """Provider-agnostic completion engine.

    接入 LLM：注册一个 completer 回调，本引擎只负责调度 + 排序 + 裁剪。
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._completers: List[Callable] = []

    def register(self, fn: Callable[[CompletionContext], List[Completion]]) -> None:
        if not callable(fn):
            raise TypeError("completer must callable")
        self._completers.append(fn)

    def complete(self, ctx: CompletionContext) -> List[Completion]:
        pool: List[Completion] = []
        for fn in self._completers:
            try:
                items = fn(ctx)
            except Exception:
                continue
            if not isinstance(items, list):
                continue
            pool.extend(c for c in items if isinstance(c, Completion))
        if not pool:
            return []
        pool.sort(key=lambda c: -c.score)
        return pool[:ctx.max_candidates]

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "completers": len(self._completers),
        }


def prefix_completer(
    snippets: Dict[str, str],
) -> Callable[[CompletionContext], List[Completion]]:
    """Simple prefix-match completer from a snippet table."""
    def _fn(ctx: CompletionContext) -> List[Completion]:
        last_line = ctx.prefix.rsplit("\n", 1)[-1]
        out: List[Completion] = []
        for key, value in snippets.items():
            if last_line.startswith(key):
                out.append(Completion(
                    text=value, score=len(key) / 20.0,
                    source="snippet_table", kind="snippet",
                ))
        return out
    return _fn


__all__ = [
    "CompletionContext", "Completion",
    "CompletionEngine", "prefix_completer",
]
