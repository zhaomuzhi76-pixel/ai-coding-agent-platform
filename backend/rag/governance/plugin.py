"""RAG 治理插件：不动现有代码，用纯函数钩子挂。"""
from __future__ import annotations

from typing import Any, Dict, Iterable

from .citations import citations_to_context, extract_citations
from .contracts import CLEARReport
from .evaluator import evaluate, evaluate_async
from .hallucination_guard import GuardDecision, guard_answer


def build_citation_context(result: dict, *, min_score: float = 0.0) -> str:
    hits = result.get("hits") if isinstance(result, dict) else None
    if not hits or not isinstance(hits, list):
        return ""
    cits = extract_citations(hits, min_score=min_score)
    if not cits:
        return ""
    return citations_to_context(cits)


def append_citation_context(
    rendered: str, result: dict, *, min_score: float = 0.0,
) -> str:
    ctx = build_citation_context(result, min_score=min_score)
    if not ctx:
        return rendered
    return f"{rendered}\n\n{ctx}"


class RagGovernancePlugin:
    VERSION = "1.0"

    def __init__(self, *, min_faithfulness: float = 0.6, strict: bool = False) -> None:
        self.min_faithfulness = min_faithfulness
        self.strict = strict

    def append_context(self, rendered: str, result: dict, *, min_score: float = 0.0) -> str:
        return append_citation_context(rendered, result, min_score=min_score)

    def guard(self, query: str, answer: str, hits: Iterable[Any]) -> GuardDecision:
        return guard_answer(
            query, answer, hits,
            min_faithfulness=self.min_faithfulness,
            strict=self.strict,
        )

    def evaluate(self, query: str, answer: str, hits: Iterable[Any]) -> CLEARReport:
        return evaluate(query, answer, hits)

    async def evaluate_async(self, query: str, answer: str, hits: Iterable[Any]) -> CLEARReport:
        return await evaluate_async(query, answer, hits)

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__, "version": self.VERSION,
            "ready": self.ready(),
            "min_faithfulness": self.min_faithfulness, "strict": self.strict,
        }


# ── RAG 结果渲染（agent_loop 原 render 不支持 dict hits）──

def _is_rag_result(result) -> bool:
    """RAG result 判定（3 层，见下行 if）。"""
    if not isinstance(result, dict):
        return False
    # 层 1：query 字段（最可靠）
    if "query" in result:
        return True
    hits = result.get("hits")
    if not isinstance(hits, list):
        return False
    # 层 2：非空 list[dict] 且首项含 chunk_id
    if hits and isinstance(hits[0], dict) and "chunk_id" in hits[0]:
        return True
    # 层 3：空 hits + count 字段（RAG 空结果）
    if not hits and "count" in result and "pattern" not in result:
        return True
    return False


def _render_rag(result: dict) -> str:
    """渲染 RAG 命中（agent_loop 原本 render 会崩，这里兜底）。"""
    hits = result.get("hits", [])
    query = str(result.get("query", ""))
    count = result.get("count", len(hits))
    lines = [f"RAG '{query}' 命中 {count} 段:"]
    for i, h in enumerate(hits, 1):
        text = str(h.get("text", "")).strip()[:300]
        src_ = h.get("source", "")
        ln = h.get("line_no", 0)
        try:
            score = float(h.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        tag = f" ({src_}:{ln})" if src_ else ""
        lines.append(f"  [{i}]{tag} score={score:.2f}  {text}")
    return "\n".join(lines)


# ── install：一键挂载（monkey-patch，0 源文件改动）──
import sys as _sys

_INSTALL_STATE: dict = {
    "installed": False,
    "patched": [],
    "orig_render": None,
}

_P2_NAME = "backend.application.agent_loop._agent_loop_parts.part2"


def install(*, auto_citation: bool = True) -> dict:
    """一键挂载：给 agent_loop 的 tool observation 自动追加 [N] 引用。

    不修改任何源文件 —— 通过替换 Python 名字绑定实现。

    原理：
        part1 通过 `from ..observation import render as render_observation` 绑定。
        part2 通过 `from .part1 import render_observation` 绑定。
        from-import 是「值绑定」→ 必须同时替换 3 处：
            1) observation.render
            2) part1.render_observation
            3) part2.render_observation（若已 import）

    用法：
        from backend.rag.governance.plugin import install
        install()
        # 之后 run_agent_loop 的每次 tool observation 都会带 [N] 引用
    """
    if _INSTALL_STATE["installed"]:
        return {"status": "already_installed",
                "patched": list(_INSTALL_STATE["patched"])}

    if not auto_citation:
        return {"status": "skipped", "reason": "auto_citation=False"}

    from backend.application.agent_loop import observation
    from backend.application.agent_loop._agent_loop_parts import part1

    _orig = observation.render
    _INSTALL_STATE["orig_render"] = _orig

    def _patched(result):
        # ── RAG 结果：agent_loop 原本 render 不支持 dict hits ──
        if _is_rag_result(result):
            ctx = build_citation_context(result)
            if ctx:
                return ctx
            return f"RAG '{result.get('query', '')}' 命中 0 段（无可靠证据）"
        # ── 其他结果：原 render + 尝试追加引用（no-op if 无 dict hits） ──
        try:
            base = _orig(result)
        except Exception as e:
            # 原 render 挂了 → 降级为 JSON（避免拖垮 agent_loop）
            import json
            return f"OBSERVATION: {json.dumps(result, ensure_ascii=False)[:2000]}"
        return append_citation_context(base, result)

    patched = []
    observation.render = _patched
    patched.append("observation.render")

    part1.render_observation = _patched
    patched.append("part1.render_observation")

    p2 = _sys.modules.get(_P2_NAME)
    if p2 is not None:
        p2.render_observation = _patched
        patched.append("part2.render_observation")

    _INSTALL_STATE["installed"] = True
    _INSTALL_STATE["patched"] = patched
    return {"status": "installed", "patched": patched}


def uninstall() -> dict:
    """还原：把 3 处绑定恢复到原始 render（用于测试隔离）。"""
    _orig = _INSTALL_STATE.get("orig_render")
    if not _INSTALL_STATE["installed"] or _orig is None:
        return {"status": "not_installed"}

    from backend.application.agent_loop import observation
    from backend.application.agent_loop._agent_loop_parts import part1

    restored = []
    observation.render = _orig
    restored.append("observation.render")

    part1.render_observation = _orig
    restored.append("part1.render_observation")

    p2 = _sys.modules.get(_P2_NAME)
    if p2 is not None:
        p2.render_observation = _orig
        restored.append("part2.render_observation")

    _INSTALL_STATE["installed"] = False
    _INSTALL_STATE["patched"] = []
    return {"status": "uninstalled", "restored": restored}


def install_status() -> dict:
    """查询挂载状态。"""
    return {
        "installed": _INSTALL_STATE["installed"],
        "patched": list(_INSTALL_STATE["patched"]),
    }


__all__ = [
    "RagGovernancePlugin",
    "build_citation_context",
    "append_citation_context",
    "install",
    "uninstall",
    "install_status",
    "_is_rag_result",
    "_render_rag",
]
