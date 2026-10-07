"""RAG Ingest API handlers（框架无关）+ FastAPI 挂载。
职责：协议解析 + 转发 L13.2 service + envelope 包装。
不实现业务、不持状态。端点独立：/api/rag/ingest/*。
"""
from __future__ import annotations
from typing import Any, Callable, Mapping, Optional

PREFIX = "/api/rag/ingest"
MAX_PATHS = 200
MAX_DIR_DEPTH = 10

def _mapping(raw: Any, name: str) -> Mapping:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must be mapping")
    return raw

def _opt_str(v: Any, key: str) -> str:
    if v is None:
        return ""
    if not isinstance(v, str):
        raise ValueError(f"{key} must be str")
    return v.strip()

def _str_list(v: Any, key: str) -> list:
    if v is None:
        return []
    if not isinstance(v, (list, tuple)):
        raise ValueError(f"{key} must be list")
    return [str(x) for x in v]

def _build_options(body: Mapping) -> Any:
    from backend.rag.ingest.service import IngestOptions
    kb = _opt_str(body.get("kb"), "kb") or "general"
    return IngestOptions(
        kb=kb,
        source=_opt_str(body.get("source"), "source"),
        batch_size=int(body.get("batch_size", 64)),
        dry_run=bool(body.get("dry_run", False)),
        skip_empty=bool(body.get("skip_empty", True)),
    )

# ---------------- handlers ----------------
def preview_handler(service: Any, raw: Any) -> dict:
    m = _mapping(raw, "body")
    path = _opt_str(m.get("path"), "path")
    if not path:
        raise ValueError("path required")
    from backend.rag.ingest.service import IngestOptions
    doc = service.preview(path, options=IngestOptions(
        kb=_opt_str(m.get("kb"), "kb") or "general", dry_run=True))
    return {
        "path": doc.path, "title": doc.title,
        "source_type": doc.source_type.value,
        "page_count": doc.page_count,
        "total_text_chars": doc.total_text_chars,
        "file_size": doc.file_size,
        "preview": [{"page_no": p.page_no, "section": p.section,
                     "chars": len(p.text), "text": p.text[:200]}
                    for p in doc.pages[:5]],
    }

def file_handler(service: Any, raw: Any) -> dict:
    m = _mapping(raw, "body")
    path = _opt_str(m.get("path"), "path")
    if not path:
        raise ValueError("path required")
    opt = _build_options(m)
    rep = service.ingest_paths([path], options=opt)
    return rep.to_dict()

def dir_handler(service: Any, raw: Any) -> dict:
    m = _mapping(raw, "body")
    directory = _opt_str(m.get("directory"), "directory")
    if not directory:
        raise ValueError("directory required")
    opt = _build_options(m)
    exts = _str_list(m.get("extensions"), "extensions") or None
    recursive = bool(m.get("recursive", True))
    rep = service.ingest_dir(directory, options=opt,
                              extensions=exts, recursive=recursive)
    return rep.to_dict()

def batch_handler(service: Any, raw: Any) -> dict:
    m = _mapping(raw, "body")
    paths = _str_list(m.get("paths"), "paths")
    if not paths:
        raise ValueError("paths required")
    if len(paths) > MAX_PATHS:
        raise ValueError(f"paths too many ({len(paths)} > {MAX_PATHS})")
    opt = _build_options(m)
    rep = service.ingest_paths(paths, options=opt)
    return rep.to_dict()

# ---------------- FastAPI ----------------
def register_ingest_routes(router: Any,
                            get_service: Callable[[], Any]) -> None:
    try:
        from fastapi import APIRouter  # noqa: F401
    except ImportError as e:
        raise RuntimeError("fastapi 未安装") from e

    def _wrap(fn):
        def _inner(*a, **kw):
            try:
                return {"ok": True, "data": fn(*a, **kw)}
            except Exception as e:
                return {"ok": False, "error": {
                    "code": type(e).__name__, "message": str(e)}}
        return _inner

    @router.post(f"{PREFIX}/preview")
    async def _preview(body: dict) -> dict:
        return _wrap(lambda: preview_handler(get_service(), body))()

    @router.post(f"{PREFIX}/file")
    async def _file(body: dict) -> dict:
        return _wrap(lambda: file_handler(get_service(), body))()

    @router.post(f"{PREFIX}/dir")
    async def _dir(body: dict) -> dict:
        return _wrap(lambda: dir_handler(get_service(), body))()

    @router.post(f"{PREFIX}/batch")
    async def _batch(body: dict) -> dict:
        return _wrap(lambda: batch_handler(get_service(), body))()

__all__ = ["PREFIX", "preview_handler", "file_handler",
           "dir_handler", "batch_handler", "register_ingest_routes"]
