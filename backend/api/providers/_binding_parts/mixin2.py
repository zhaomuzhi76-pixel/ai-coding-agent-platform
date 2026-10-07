"""Mixin 2 of ProviderBinding."""
from __future__ import annotations
from .part1 import (Any, Dict, get_checker, get_tracker, load_llm_config, test_provider,)  # noqa: F401
class _Mixin2:
    async def local_models(
        self, name: str, base_url: str = "",
    ) -> Dict[str, Any]:
        """返回该 provider 的本机可用模型列表。

        - 优先按 name 从 yaml 找
        - 找不到则用传入的 base_url（新 provider 未保存时用）
        - ollama 类型：调 /api/tags 实时发现
        """
        name = str(name or "").strip()
        base_url = str(base_url or "").strip()
        if not name and not base_url:
            raise ValueError("provider name or base_url required")

        from backend.providers.config import load_llm_config
        cfg = load_llm_config()
        target = None
        for _p in cfg.providers:
            if _p.name == name:
                target = _p
                break

        # 找不到但传了 base_url → 当 ollama 处理
        if target is None:
            if not base_url:
                raise KeyError(f"provider not found: {name}")
            try:
                from backend.providers.discovery.ollama_discovery import (
                    discover_ollama_models,
                )
                discovered = await discover_ollama_models(base_url)
                return {
                    "provider": name or "(new)",
                    "type": "ollama",
                    "source": "discovery",
                    "models": [
                        {
                            "id": d.get("id", ""),
                            "display_name": d.get("display_name", ""),
                            "context_window": d.get("context_window", 0),
                        }
                        for d in discovered
                        if not str(d.get("id", "")).startswith("__")
                    ],
                }
            except Exception as exc:
                return {"provider": name or "(new)", "type": "ollama",
                        "source": "discovery", "error": str(exc),
                        "models": []}

        # ollama → 实时发现
        if target.type == "ollama":
            try:
                from backend.providers.discovery.ollama_discovery import (
                    discover_ollama_models,
                )
                discovered = await discover_ollama_models(target.base_url)
                return {
                    "provider": name,
                    "type": "ollama",
                    "source": "discovery",
                    "models": [
                        {
                            "id": d.get("id", ""),
                            "display_name": d.get("display_name", ""),
                            "context_window": d.get("context_window", 0),
                        }
                        for d in discovered
                        if not str(d.get("id", "")).startswith("__")
                    ],
                }
            except Exception as exc:
                return {
                    "provider": name, "type": "ollama",
                    "source": "discovery", "error": str(exc),
                    "models": [],
                }

        # 其他类型 → 返回 yaml 声明的
        return {
            "provider": name,
            "type": target.type,
            "source": "yaml",
            "models": [
                {
                    "id": m.id,
                    "display_name": m.display_name,
                    "context_window": m.context_window,
                }
                for m in target.models
                if not str(m.id).startswith("__")
            ],
        }

    async def health(self) -> Dict[str, Any]:
        checker = get_checker()
        records = await checker.check_all()
        return {"records": [r.to_dict() for r in records],
                "count": len(records)}

    def health_cached(self) -> Dict[str, Any]:
        return {"snapshot": get_checker().cache.snapshot()}

    def cost(self) -> Dict[str, Any]:
        return get_tracker().stats()

    def raw_yaml(self) -> Dict[str, Any]:
        """返回 yaml 原文 + 文件路径。"""
        path = self._editor.path
        if not path.is_file():
            return {"path": str(path), "text": ""}
        with path.open("r", encoding="utf-8") as fh:
            return {"path": str(path), "text": fh.read()}

    def upsert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """新增或更新 provider。

        工业级契约：
          - 只写 yaml，不碰白名单（白名单由 router 的测试结果管理）
          - 前端保存前必须测试通过（按钮已限制）
        """
        entry = self._editor.upsert(payload)
        return {"saved": True, "provider": entry}

    def delete(self, name: str) -> Dict[str, Any]:
        ok = self._editor.delete(name)
        if ok:
            from backend.api.providers.verified_store import get_store
            get_store().unmark(name)
        return {"deleted": ok, "name": name}

    async def test(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """测试 provider 连接。

        工业级契约：
          - 通过 → 写入 verified 白名单 → 主页下拉立刻可见
          - 失败 → 清除白名单记录 → 主页下拉隐藏
        """
        result = await test_provider(payload)
        name = str(payload.get("name", "")).strip()
        if name:
            from backend.api.providers.verified_store import get_store
            store = get_store()
            if result.get("success"):
                store.mark(
                    name,
                    latency_ms=float(
                        result.get("latency_ms", 0.0) or 0.0
                    ),
                )
            else:
                store.unmark(name)
        return result

    def verified(self) -> Dict[str, Any]:
        """返回白名单快照（配置页展示用）。"""
        from backend.api.providers.verified_store import get_store
        snap = get_store().snapshot()
        return {"verified": snap, "count": len(snap)}

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }
