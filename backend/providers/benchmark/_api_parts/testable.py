"""可测模型列表 —— 严格白名单 + 30 秒缓存"""
import time
from typing import Any, Dict, List

BLACKLIST_TOKENS = (
    "embed", "embedding", "rerank", "reranker", "bge-", "nomic-embed",
    "mxbai-embed", "text-embedding", "text-rerank",
    "whisper", "tts", "asr", "speech", "audio", "voice", "s2s",
    "livetranslate", "translate", "mt-", "mt_", "realtime",
    "image", "wan2", "stable-diffusion", "dall-e", "clip",
    "z-image", "qwen-image", "qwen-vl-ocr",
    "ocr", "omni-flash", "omni-turbo", "character", "gui-",
    "deep-research", "deep-search", "research",
    "mimo", "unisound",
    "qwen1.5", "qwen-1.8b", "qwen2-", "qwen-7b", "qwen-14b",
    "qwen-72b", "qwen-math", "qwen-vl-", "qwq-", "qvq-", "qwen-long",
)

_cache: Dict[str, Any] = {"ts": 0.0, "data": []}
_CACHE_TTL = 30.0


def _is_chat(mid: str, display: str = "") -> bool:
    low = (mid + " " + display).lower()
    return not any(tok in low for tok in BLACKLIST_TOKENS)


def _auto_verify_connected(reg) -> None:
    try:
        health = reg.health()
    except Exception:
        return
    for pid, ok in health.items():
        if not ok:
            continue
        pms = [m.id for m in reg.models.values() if m.provider_id == pid]
        if pms and all(reg.verification.is_verified(mid) for mid in pms):
            continue
        try:
            reg.test_and_verify(pid)
        except Exception:
            continue


def _load() -> List[Dict[str, Any]]:
    try:
        from backend.core.model_registry.registry import get_registry
        from backend.core.model_registry.bootstrap import bootstrap_default
        reg = get_registry()
        if not reg.providers:
            bootstrap_default()
        reg.discover_models()
        if not reg.verification.list_verified():
            _auto_verify_connected(reg)
    except Exception as e:
        print(f"[testable] registry 失败: {e}", flush=True)
        return []

    verified = set(reg.verification.list_verified())
    by_p: Dict[str, List[Dict[str, Any]]] = {}
    for m in reg.models.values():
        if m.id not in verified:
            continue
        if not _is_chat(m.id, m.display_name):
            continue
        prov = reg.providers.get(m.provider_id)
        if not prov:
            continue
        by_p.setdefault(m.provider_id, []).append({
            "provider": m.provider_id, "model": m.id,
            "type": prov.kind,
            "display_name": m.display_name or m.id,
            "is_local": prov.kind in ("ollama", "local", "ollama-local",
                                       "vllm", "lmstudio"),
            "is_healthy": True,
        })
    out: List[Dict[str, Any]] = []
    for pid, items in by_p.items():
        items.sort(key=lambda x: (not x["is_local"], x["model"]))
        out.extend(items[:50])
    return out


def list_testable_from_registry(use_cache: bool = True) -> List[Dict[str, Any]]:
    if use_cache and time.time() - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]
    data = _load()
    _cache["ts"] = time.time()
    _cache["data"] = data
    return data


def invalidate_cache() -> None:
    _cache["ts"] = 0.0
    _cache["data"] = []
