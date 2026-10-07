"""自定义 MCP 工具注册（JSON 存储，原子写入）"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

STORE = Path(os.environ.get(
    "BIANCHENG_MCP_CUSTOM",
    str(Path.home() / ".biancheng" / "mcp_custom_tools.json"),
))


def _load() -> Dict[str, Any]:
    if not STORE.exists():
        return {"tools": {}, "disabled": []}
    try:
        d = json.loads(STORE.read_text(encoding="utf-8"))
        d.setdefault("tools", {})
        d.setdefault("disabled", [])
        return d
    except Exception:
        return {"tools": {}, "disabled": []}


def _save(data: Dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(STORE.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STORE)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def list_custom() -> List[Dict[str, Any]]:
    return list(_load()["tools"].values())


def get_custom(name: str) -> Optional[Dict[str, Any]]:
    return _load()["tools"].get(name)


def register_custom(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValueError("name 必填")
    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValueError("name 只能字母/数字/下划线/中划线")
    data = _load()
    tool = {
        "name": name,
        "description": payload.get("description", ""),
        "category": "custom",
        "params": payload.get("params", []),
        "code": payload.get("code", ""),
        "exposed": True,
        "custom": True,
    }
    data["tools"][name] = tool
    _save(data)
    return tool


def delete_custom(name: str) -> bool:
    data = _load()
    if name not in data["tools"]:
        return False
    del data["tools"][name]
    disabled = set(data.get("disabled", []))
    disabled.discard(name)
    data["disabled"] = sorted(disabled)
    _save(data)
    return True


def toggle_tool(name: str, enabled: bool) -> None:
    data = _load()
    disabled = set(data.get("disabled", []))
    if enabled:
        disabled.discard(name)
    else:
        disabled.add(name)
    data["disabled"] = sorted(disabled)
    _save(data)


def list_disabled() -> List[str]:
    return list(_load().get("disabled", []))
