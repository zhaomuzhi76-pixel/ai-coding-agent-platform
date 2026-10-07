"""Provider 验证白名单。

工业级契约：
  - 只有用户主动"测试连接"通过的 provider 才进白名单
  - 主页下拉只显示白名单里的模型
  - 原子写：先 .tmp 再 os.replace，防并发损坏
  - 首次启动从 yaml 迁移（避免升级后主页全空）
  - upsert/delete 时自动清除
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Optional


class VerifiedStore:
    VERSION = "1.0"

    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            base = Path(__file__).resolve().parents[3]
            path = base / "backend" / "config" / ".verified.json"
        self.path = Path(path)
        self._lock = threading.Lock()
        self._cache: Optional[dict] = None

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        if not self.path.is_file():
            self._cache = {"version": 1, "providers": {}}
            return self._cache
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {"version": 1, "providers": {}}
            data.setdefault("providers", {})
            self._cache = data
        except Exception:
            self._cache = {"version": 1, "providers": {}}
        return self._cache

    def _save_locked(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)
        self._cache = data

    def mark(
        self, name: str, latency_ms: float = 0.0,
        models: Optional[list[str]] = None,
    ) -> None:
        with self._lock:
            data = self._load()
            data["providers"][name] = {
                "verified_at": time.time(),
                "latency_ms": float(latency_ms),
                "models": list(models or []),
            }
            self._save_locked(data)

    def unmark(self, name: str) -> None:
        with self._lock:
            data = self._load()
            if name in data["providers"]:
                del data["providers"][name]
                self._save_locked(data)

    def is_verified(self, name: str) -> bool:
        return name in self._load()["providers"]

    def all_verified(self) -> set[str]:
        return set(self._load()["providers"].keys())

    def snapshot(self) -> dict:
        return dict(self._load()["providers"])

    def migrate_from_config(self, provider_names: list[str]) -> int:
        """首次启动：把 yaml 里现有 provider 一次性标记。"""
        with self._lock:
            data = self._load()
            added = 0
            for name in provider_names:
                if name not in data["providers"]:
                    data["providers"][name] = {
                        "verified_at": time.time(),
                        "latency_ms": 0.0,
                        "models": [],
                        "migrated": True,
                    }
                    added += 1
            if added:
                self._save_locked(data)
            return added


_STORE: Optional[VerifiedStore] = None


def get_store() -> VerifiedStore:
    global _STORE
    if _STORE is None:
        _STORE = VerifiedStore()
    return _STORE


def reset() -> None:
    global _STORE
    _STORE = None


__all__ = ["VerifiedStore", "get_store", "reset"]
