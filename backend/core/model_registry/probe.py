"""临时 Provider 探测（不落盘，不修改 registry）"""
import time
from typing import Any, Dict

from .domain import ProviderConfig
from .plugins import get_plugin_class


def _resolve_api_key(payload: Dict[str, Any], api_key: str) -> str:
    """编辑模式：若前端没传新 key，用 registry 里已存的"""
    if api_key:
        return api_key
    existing_id = payload.get("existing_id", "")
    if not existing_id:
        return ""
    try:
        from .registry import get_registry
        old = get_registry().providers.get(existing_id)
        return old.api_key if old else ""
    except Exception:
        return ""


def probe_provider(payload: Dict[str, Any]) -> Dict[str, Any]:
    kind = (payload.get("kind") or "").strip()
    base_url = (payload.get("base_url") or "").strip()
    api_key = _resolve_api_key(payload, payload.get("api_key") or "")

    if not kind:
        return {"ok": False, "error": "缺少类型"}
    if not base_url:
        return {"ok": False, "error": "缺少 base_url"}

    cls = get_plugin_class(kind)
    if cls is None:
        return {"ok": False, "error": f"未知类型: {kind}"}

    cfg = ProviderConfig(
        id="__probe__", name="probe", kind=kind,
        base_url=base_url, api_key=api_key,
    )
    plugin = cls(cfg)

    start = time.time()
    try:
        ok = plugin.test_connection()
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "latency_ms": ms}

    ms = int((time.time() - start) * 1000)
    if not ok:
        return {"ok": False, "error": "连接失败（URL 不可达或 API Key 无效）",
                "latency_ms": ms}

    models = []
    try:
        for m in plugin.fetch_models():
            models.append({"id": m.id, "display": m.display_name or m.id})
    except Exception:
        pass

    return {"ok": True, "latency_ms": ms, "model_count": len(models),
            "models": models[:50]}
