"""模型注册中心 - 统一管理 Provider / Model / RoleRoute"""
from typing import Dict, List, Optional

from .domain import ModelInfo, ProviderConfig, RoleRoute
from .plugins import BaseProviderPlugin, get_plugin_class
from .verification import VerificationStore


class ModelRegistry:
    def __init__(self):
        self.providers: Dict[str, ProviderConfig] = {}
        self.plugins: Dict[str, BaseProviderPlugin] = {}
        self.models: Dict[str, ModelInfo] = {}
        self.roles: Dict[str, RoleRoute] = {}
        self.verification = VerificationStore()

    def register_provider(self, config: ProviderConfig) -> None:
        cls = get_plugin_class(config.kind)
        if cls is None:
            raise ValueError(f"Unknown provider kind: {config.kind}")
        self.providers[config.id] = config
        self.plugins[config.id] = cls(config)

    def discover_models(self) -> List[ModelInfo]:
        found: List[ModelInfo] = []
        for pid, plugin in self.plugins.items():
            if not self.providers[pid].enabled:
                continue
            for m in plugin.fetch_models():
                self.models[m.id] = m
                found.append(m)
        return found

    def set_role_route(self, route: RoleRoute) -> None:
        self.roles[route.role] = route

    def get_role_route(self, role: str) -> Optional[RoleRoute]:
        return self.roles.get(role)

    def resolve(self, role: str) -> Optional[ModelInfo]:
        route = self.roles.get(role)
        return self.models.get(route.primary) if route else None

    def resolve_provider(self, role: str) -> str:
        m = self.resolve(role)
        return m.provider_id if m else ""

    def test_and_verify(self, provider_id: str) -> Dict:
        plugin = self.plugins.get(provider_id)
        if not plugin:
            return {"ok": False, "error": "provider not found"}
        provider_models = [m.id for m in self.models.values()
                           if m.provider_id == provider_id]
        err_msg = "connection failed"
        try:
            ok = plugin.test_connection()
        except Exception as exc:
            ok = False
            err_msg = f"{type(exc).__name__}: {exc}"
        if ok:
            self.verification.mark_verified(provider_models)
            return {"ok": True, "provider": provider_id,
                    "verified": provider_models}
        for mid in provider_models:
            self.verification.mark_failed(mid, err_msg)
        return {"ok": False, "provider": provider_id,
                "failed": provider_models, "error": err_msg}

    # 非 chat 能力关键词（不进入 Agent 下拉）
    _NON_CHAT_TOKENS = (
        "embed", "embedding", "rerank", "reranker",
        "clip", "bge-", "nomic-embed", "mxbai-embed",
        "whisper", "tts", "stable-diffusion",
    )

    @classmethod
    def _is_chat_model(cls, model_id: str, display: str = "") -> bool:
        """判定是否为 chat 模型：过滤 embedding / reranker / 视觉专用等"""
        low = (model_id + " " + display).lower()
        return not any(tok in low for tok in cls._NON_CHAT_TOKENS)

    def list_verified_models(self, chat_only: bool = True) -> List[Dict]:
        out = []
        for mid in self.verification.list_verified():
            m = self.models.get(mid)
            if not m:
                continue
            if chat_only and not self._is_chat_model(m.id, m.display_name):
                continue
            out.append({
                "id": m.id,
                "provider": m.provider_id,
                "display_name": f"{m.id} · {m.provider_id}",
                "label": f"{m.display_name or m.id} · {m.provider_id}",
            })
        return out

    def health(self) -> Dict[str, bool]:
        return {pid: p.test_connection() for pid, p in self.plugins.items()}

    def generate(self, role: str, prompt: str, **kwargs) -> str:
        """工业级容灾：primary 抛异常自动降级到 fallback，最后再抛"""
        route = self.roles.get(role)
        if not route:
            raise KeyError(f"Role not routed: {role}")
        errors = []
        for mid in (route.primary, route.fallback):
            if not mid:
                continue
            m = self.models.get(mid)
            if not m:
                errors.append(f"unknown model: {mid}")
                continue
            plugin = self.plugins.get(m.provider_id)
            if not plugin:
                errors.append(f"no plugin for: {m.provider_id}")
                continue
            import time as _t
            _start = _t.time()
            _online = m.provider_id not in ("ollama-local", "local")
            try:
                result = plugin.generate(mid, prompt, **kwargs)
                try:
                    from backend.monitor.recorder import record_call
                    record_call(m.provider_id, mid,
                                latency_ms=int((_t.time() - _start) * 1000),
                                success=True, online=_online)
                except Exception:
                    pass
                return result
            except Exception as exc:  # noqa: BLE001 容灾路径必须全捕获
                try:
                    from backend.monitor.recorder import record_call
                    record_call(m.provider_id, mid,
                                latency_ms=int((_t.time() - _start) * 1000),
                                success=False, error=str(exc), online=_online)
                except Exception:
                    pass
                errors.append(f"{mid}: {type(exc).__name__}: {exc}")
                continue
        raise RuntimeError(
            f"No available model for role '{role}': " + " | ".join(errors)
        )


_singleton: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """获取注册中心单例。

    首次创建时自动：
      1. bootstrap（注册默认 Provider）
      2. load 持久化文件（覆盖默认值，包含用户改过的 role routing）
    """
    global _singleton
    if _singleton is None:
        _singleton = ModelRegistry()
        # 1) 引导默认 Provider
        try:
            from .bootstrap import bootstrap_default
            bootstrap_default()
        except Exception:
            pass
        # 2) 覆盖为持久化配置（用户改过的 role 在这里生效）
        try:
            from .persistence import load as _load
            _load(_singleton)
        except Exception:
            pass
    return _singleton


def reset_registry() -> None:
    global _singleton
    _singleton = None
