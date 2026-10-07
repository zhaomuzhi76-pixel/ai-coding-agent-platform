"""ProviderEditor: 读写 llm_providers.yaml。

api_key 支持：
    - 明文 "sk-xxx"
    - 环境变量引用 "${DASHSCOPE_API_KEY}"
    - "__KEEP__"  哨兵：保留原值（前端不改 key 时用）
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


_DEFAULT_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "llm_providers.yaml"
)

_VALID_TYPES = {
    "ollama", "openai_compatible", "dashscope", "anthropic",
    "deepseek", "gemini",
}


def _load(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"providers": []}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _save(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            data, fh,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


class ProviderEditor:
    VERSION = "1.0"

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or _DEFAULT_PATH

    def read(self) -> Dict[str, Any]:
        return _load(self.path)

    def upsert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        ptype = str(payload.get("type", "")).strip()
        if not name:
            raise ValueError("provider.name required")
        if ptype not in _VALID_TYPES:
            raise ValueError(
                f"unsupported type: {ptype} (allowed {sorted(_VALID_TYPES)})"
            )
        base_url = str(payload.get("base_url", "")).strip()
        api_key = str(payload.get("api_key", "")).strip()
        display_name = str(payload.get("display_name", name)).strip()
        models = payload.get("models") or []
        if not isinstance(models, list) or not models:
            raise ValueError("at least one model required")

        data = _load(self.path)
        providers: List[Dict[str, Any]] = data.setdefault("providers", [])
        existing_idx = next(
            (i for i, p in enumerate(providers) if p.get("name") == name),
            -1,
        )

        # api_key 保留原值逻辑
        if api_key == "__KEEP__" and existing_idx >= 0:
            api_key = str(providers[existing_idx].get("api_key", ""))

        entry = {
            "name": name,
            "type": ptype,
            "display_name": display_name,
            "base_url": base_url,
            "api_key": api_key,
            "models": models,
        }

        if existing_idx >= 0:
            providers[existing_idx] = entry
        else:
            providers.append(entry)

        _save(self.path, data)
        return entry

    def delete(self, name: str) -> bool:
        name = (name or "").strip()
        if not name:
            raise ValueError("provider name required")
        data = _load(self.path)
        providers = data.get("providers", [])
        before = len(providers)
        data["providers"] = [p for p in providers if p.get("name") != name]
        if len(data["providers"]) == before:
            return False
        _save(self.path, data)
        return True

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {"name": type(self).__name__, "path": str(self.path)}


__all__ = ["ProviderEditor"]
