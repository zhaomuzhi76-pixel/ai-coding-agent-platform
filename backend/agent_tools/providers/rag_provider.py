"""RAG 命名空间 → Agent 工具 provider。
职责：把"RAG 命名空间定义"翻译为 ToolDescriptor 列表 + 执行入口。
不做注册（registry 管）、不调 MCP（client 管）、不组装最终响应（agent_loop 管）。
空库/后端不可用时短路，返回 ok=True 的可读消息，不让 Agent 崩。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from backend.agent_tools.contracts import (
    ToolCall, ToolCategory, ToolDescriptor, ToolDomain, ToolResult)

@dataclass(frozen=True)
class RagToolSpec:
    tool_name: str
    description: str
    domain: ToolDomain
    where: Optional[dict] = None
    top_k: int = 5
    rerank: bool = True

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("RagToolSpec.tool_name required")
        if not self.description.strip():
            raise ValueError("RagToolSpec.description required")
        if self.top_k <= 0:
            raise ValueError("RagToolSpec.top_k must be > 0")

def _svc_ready(svc: Any) -> tuple:
    """返回 (ready, count)。任一失败 → (False, -1)。"""
    try:
        st = svc.status()
        ready = bool(getattr(st, "ready", False))
        count = int(getattr(st, "indexed", -1))
        return ready, count
    except Exception:
        return False, -1



def _try_hybrid_or_default(svc, query, *, limit, where, rerank):
    """优先 svc.search（保证 images 字段）；无结果时降级 hybrid。

    2026-09 变更：
        hybrid 层构造 HybridHit 时丢弃了 images 字段（只保留文本 metadata），
        导致 RAG tool 无法向 agent 返回图片。
        改为**优先 svc.search**（返回 MultimodalHit，含完整 images）。
        只有 svc.search 完全无结果时才用 hybrid（BM25 补充）。
    """
    # 1) 优先 svc.search —— 含 images
    try:
        rep = svc.search(query, limit=limit, where=where, rerank=rerank)
        hits = list(getattr(rep, "hits", ()) or ())
        if hits:
            return rep
    except Exception:
        pass
    # 2) svc 无结果 → 降级 hybrid（作为语义/BM25 补充）
    try:
        from backend.rag.hybrid.runtime import (
            get_hybrid_runtime, ensure_synced)
        ensure_synced()
        rt = get_hybrid_runtime()
        return rt.retriever.search(query, top_k=limit, where=where)
    except Exception:
        return svc.search(query, limit=limit,
                          where=where, rerank=rerank)


class RagToolProvider:
    def __init__(self, service: Any, specs: Sequence[RagToolSpec]) -> None:
        if service is None:
            raise ValueError("service required")
        if not specs:
            raise ValueError("specs required")
        self._svc = service
        self._specs = tuple(specs)
        self._by_name = {s.tool_name: s for s in specs}
        if len(self._by_name) != len(self._specs):
            raise ValueError("RagToolSpec.tool_name must be unique")

    def descriptors(self) -> list[ToolDescriptor]:
        return [
            ToolDescriptor(
                name=s.tool_name, description=s.description,
                category=ToolCategory.RAG, domain=s.domain,
                server="local", tags=("rag",),
                meta={"where": s.where or {}, "top_k": s.top_k},
            )
            for s in self._specs
        ]

    def can_handle(self, name: str) -> bool:
        return name in self._by_name

    def execute(self, call: ToolCall) -> ToolResult:
        spec = self._by_name.get(call.name)
        if spec is None:
            return ToolResult(name=call.name, ok=False,
                              error=f"unknown rag tool: {call.name}")
        # 兼容 query / q / keyword / term 键名
        query = str(call.arguments.get("query")
                    or call.arguments.get("q")
                    or call.arguments.get("keyword")
                    or call.arguments.get("term") or "").strip()
        if not query:
            return ToolResult(name=call.name, ok=False, error="query required")

        # 空库短路：不真调 embedding
        ready, count = _svc_ready(self._svc)
        if not ready or count == 0:
            return ToolResult(
                name=call.name, ok=True,
                output=f"(知识库暂无「{query}」相关内容)",
                meta={"hit_count": 0, "query": query,
                      "degraded": True,
                      "reason": "vector store empty or unavailable"})

        try:
            limit = int(call.arguments.get("limit", spec.top_k) or spec.top_k)
        except (TypeError, ValueError):
            limit = spec.top_k
        try:
            rep = _try_hybrid_or_default(
                self._svc, query, limit=limit,
                where=spec.where, rerank=spec.rerank)
        except Exception as e:
            return ToolResult(
                name=call.name, ok=True,
                output=f"(知识库暂无「{query}」相关内容)",
                meta={"hit_count": 0, "query": query,
                      "degraded": True,
                      "reason": f"{type(e).__name__}: {e}"})
        hits = list(getattr(rep, "hits", ()) or [])
        lines = []
        images = []
        for i, h in enumerate(hits):
            txt = (getattr(h, "text", "") or "").strip()
            if txt:
                lines.append(f"[{i + 1}] {txt}")
            for ref in (getattr(h, "images", ()) or ()):
                try:
                    images.append({
                        "id": str(getattr(ref, "id", "")),
                        "mime": str(getattr(ref, "mime", "image/png")),
                        "url": getattr(ref, "url", None),
                        "b64": getattr(ref, "b64", None),
                        "alt_text": str(getattr(ref, "alt_text", "")),
                        "_hit_text": (getattr(h, "text", "") or ""),
                    })
                except Exception:
                    pass
        # 按 query 相关性过滤（避免"玉米"带出小麦/水稻图）
        images = _filter_images(query, images, max_images=2)
        out = "\n".join(lines) if lines else f"(知识库暂无「{query}」相关内容)"
        return ToolResult(
            name=call.name, ok=True, output=out,
            meta={"hit_count": len(hits), "query": query,
                  "images": images})

def make_rag_provider(service: Any,
                      specs: Sequence[RagToolSpec]) -> RagToolProvider:
    return RagToolProvider(service, specs)

def _filter_images(query: str, images: list, *, max_images: int = 2) -> list:
    """按 query token 过滤图片。委托 image_selector 逻辑（保持单一职责）。"""
    if not images:
        return []
    try:
        from backend.runtime.plugins.chatbot.image_selector import (
            filter_relevant_images)

        class _Wrap:
            __slots__ = ("id", "mime", "url", "b64", "alt_text")
            def __init__(self, d):
                self.id = d["id"]
                self.mime = d["mime"]
                self.url = d.get("url")
                self.b64 = d.get("b64")
                self.alt_text = d.get("alt_text", "")

        wrapped = [_Wrap(d) for d in images]
        texts = [d.get("_hit_text", "") for d in images]
        kept = filter_relevant_images(
            query, wrapped, hit_texts=texts, max_images=max_images)
        # 保留原 dict 引用
        kept_ids = {w.id for w in kept}
        out = []
        for d in images:
            if d["id"] in kept_ids:
                d2 = {k: v for k, v in d.items() if k != "_hit_text"}
                out.append(d2)
        return out
    except Exception:
        # 过滤失败 → 兜底返回前 N 张
        return [{k: v for k, v in d.items() if k != "_hit_text"}
                for d in images[:max_images]]


__all__ = ["RagToolProvider", "RagToolSpec", "make_rag_provider"]
