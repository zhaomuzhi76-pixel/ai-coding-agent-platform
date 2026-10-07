"""Mixin 1 of ProviderBinding."""
from __future__ import annotations
from .part1 import (Any, Dict, ProviderEditor, load_llm_config,)  # noqa: F401
class _Mixin1:
    def __init__(self) -> None:
        self._editor = ProviderEditor()

    def config(self) -> Dict[str, Any]:
        cfg = load_llm_config()
        return {
            "source": cfg.source,
            "default_provider": cfg.default_provider,
            "default_model": cfg.default_model,
            "providers": [p.to_dict() for p in cfg.providers],
            "skipped": list(cfg.skipped),
            "agent_routing": {
                role: [r.to_dict() for r in chain]
                for role, chain in cfg.agent_routing.items()
            },
            "embeddings": [e.to_dict() for e in cfg.embeddings],
            "rerankers": [r.to_dict() for r in cfg.rerankers],
            "vector_store": cfg.vector_store.to_dict(),
        }

    def models(self) -> Dict[str, Any]:
        # ── 自动补齐白名单：yaml 里有但白名单没有的 provider，纳入白名单 ──
        # 工业级契约：yaml 是用户意图，白名单是运行时过滤。
        # 用户主动在 yaml 里写了 provider（不论何时），就应视为"已配置"。
        try:
            from backend.api.providers.verified_store import get_store
            from backend.providers.config import load_llm_config as _load
            _cfg = _load()
            _store = get_store()
            _verified_now = _store.all_verified()
            _added = []
            for _p in _cfg.providers:
                # 哨兵 provider（ollama 空 models）也要纳入
                if _p.name not in _verified_now:
                    _store.mark(_p.name, latency_ms=0.0, models=[])
                    _added.append(_p.name)
            if _added:
                print(
                    f"[binding] auto-verified new providers: {_added}",
                    flush=True,
                )
        except Exception as exc:
            print(
                f"[binding] auto-verify failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

        cfg = load_llm_config()
        discovered: Dict[str, Any] = {}
        # 合并 discovery 发现的模型（yaml 里没写的自动补上）
        try:
            from backend.providers.discovery import (
                get_all_discovered,
                merge_into_config,
            )
            discovered = get_all_discovered() or {}
            if discovered:
                cfg = merge_into_config(cfg, discovered)
        except Exception as exc:
            # 不静默：import 失败要暴露（之前静默吞掉导致 30 分钟排查）
            print(
                f"[binding] discovery merge failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
            discovered = {}

        # 只返回 verified 白名单里的 provider 的模型
        try:
            from backend.api.providers.verified_store import get_store
            _store = get_store()
            verified = _store.all_verified()
            snapshot = _store.snapshot()   # {provider: {models: [...], ...}}
        except Exception:
            verified = set()
            snapshot = {}

        all_models = cfg.all_models()
        all_models = [
            m for m in all_models
            if not str(m.get("model", "")).startswith("__")
        ]

        # 静态 provider（yaml 里显式写 models，如 openai_compatible / anthropic）
        # → provider 在白名单即显示
        # 动态 provider（ollama，yaml models 为空，靠发现）
        # → 必须 verified_store.models 列表非空且包含该模型才显示
        static_providers = set()
        for _p in cfg.providers:
            if _p.type == "ollama":
                continue
            # yaml 里 models 非空 → 静态
            if getattr(_p, "models", None):
                static_providers.add(_p.name)

        filtered = []
        for m in all_models:
            provider = str(m.get("provider", ""))
            if provider not in verified:
                continue
            if provider in static_providers:
                filtered.append(m)
                continue
            # 动态 provider：要求子级模型白名单
            allowed = list(
                (snapshot.get(provider) or {}).get("models") or []
            )
            if allowed and str(m.get("model", "")) in allowed:
                filtered.append(m)

        return {"models": filtered}
