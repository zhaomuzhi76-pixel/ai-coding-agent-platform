"""图文 RAG API 层。职责：协议解析 + 转发 L7.4 service + 序列化。
不实现业务、不做路由选择、不持有 service（依赖注入）。
端点独立于现有 /api/rag/*（纯文本），命名空间为 /api/rag/multimodal/*。"""
from __future__ import annotations
from typing import Any, Callable, Mapping, Optional

PREFIX = "/api/rag/multimodal"
DEFAULT_LIMIT = 5
MAX_LIMIT = 100

def _require_mapping(raw: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return raw

def parse_search_body(raw: Any) -> dict:
    m = _require_mapping(raw, "search body")
    q = m.get("query", "")
    if not isinstance(q, str) or not q.strip():
        raise ValueError("query must be non-empty str")
    limit = m.get("limit", DEFAULT_LIMIT)
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("limit must be int")
    if limit <= 0 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be 1..{MAX_LIMIT}")
    rerank = bool(m.get("rerank", False))
    rtk = m.get("rerank_top_k", 0)
    if not isinstance(rtk, int) or isinstance(rtk, bool) or rtk < 0:
        raise ValueError("rerank_top_k must be int >= 0")
    where = m.get("where")
    if where is not None and not isinstance(where, Mapping):
        raise ValueError("where must be mapping or null")
    return {"query": q.strip(), "limit": limit, "rerank": rerank,
            "rerank_top_k": rtk, "where": dict(where) if where else None}

def parse_index_body(raw: Any) -> dict:
    """两种形态：
      A) {"items": [{text, images, ...}, ...]} —— 批量
      B) {"text": "...", "images": [...], "source": "...", ...} —— 单条
    """
    m = _require_mapping(raw, "index body")
    if "items" in m:
        items = m["items"]
        if not isinstance(items, (list, tuple)):
            raise ValueError("items must be list")
        return {"items": list(items), "batch_size": int(m.get("batch_size", 64))}
    text = m.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be non-empty str（或提供 items）")
    return {
        "text": text, "images": m.get("images"),
        "source": str(m.get("source", "")),
        "source_path": str(m.get("source_path", "")),
        "line_no": int(m.get("line_no", 0)),
        "role": str(m.get("role", "")),
        "metadata": dict(m.get("metadata") or {}),
        "batch_size": int(m.get("batch_size", 64)),
    }

def index_handler(service: Any, raw_body: Any) -> dict:
    body = parse_index_body(raw_body)
    if "items" in body:
        rep = service.index_items(body["items"],
                                   batch_size=body["batch_size"])
    else:
        bs = body.pop("batch_size")
        rep = service.index_text(**body, batch_size=bs)
    return {"indexed": rep.indexed, "chunks": rep.chunks,
            "skipped": rep.skipped, "batches": rep.batches,
            "errors": list(rep.errors)}

def search_handler(service: Any, raw_body: Any) -> dict:
    p = parse_search_body(raw_body)
    return service.search_dict(p["query"], limit=p["limit"], where=p["where"],
                                rerank=p["rerank"],
                                rerank_top_k=p["rerank_top_k"])

def status_handler(service: Any) -> dict:
    st = service.status()
    return {"ready": st.ready, "indexed": st.indexed,
            "has_embed": st.has_embed, "has_rerank": st.has_rerank}

def register_multimodal_routes(router: Any,
                                get_service: Callable[[], Any]) -> None:
    """FastAPI 挂载。未安装 fastapi 时抛错，不影响本模块导入。"""
    try:
        from fastapi import APIRouter  # noqa: F401
    except ImportError as e:
        raise RuntimeError("fastapi 未安装，无法挂载 multimodal rag routes") from e

    def _envelope(fn):
        def _wrap():
            try:
                return {"ok": True, "data": fn()}
            except Exception as e:
                return {"ok": False,
                        "error": {"code": type(e).__name__, "message": str(e)}}
        return _wrap

    @router.post(f"{PREFIX}/index")
    async def _index(body: dict) -> dict:
        return _envelope(lambda: index_handler(get_service(), body))()

    @router.post(f"{PREFIX}/search")
    async def _search(body: dict) -> dict:
        return _envelope(lambda: search_handler(get_service(), body))()

    @router.get(f"{PREFIX}/status")
    async def _status() -> dict:
        return _envelope(lambda: status_handler(get_service()))()

__all__ = ["PREFIX", "parse_index_body", "parse_search_body",
           "index_handler", "search_handler", "status_handler",
           "register_multimodal_routes"]
