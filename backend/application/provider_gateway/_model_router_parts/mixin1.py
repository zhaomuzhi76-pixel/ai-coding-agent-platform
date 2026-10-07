"""Mixin 1 of ModelRouter."""
from __future__ import annotations
from .part1 import (Any, Dict, List, Optional, estimate_messages, estimate_tokens, get_tracker, load_llm_config, time,)  # noqa: F401
class _Mixin1:
    def __init__(
        self,
        *,
        override_model: Optional[str] = None,
        override_provider: Optional[str] = None,
        user_routing: Any = None,
    ) -> None:
        self._config = load_llm_config()
        self._override_model = (override_model or "").strip()
        self._override_provider = (override_provider or "").strip()
        # user_routing: UserRouting 对象 or None
        self._user_routing = user_routing
        self.call_count = 0
        self.fallback_count = 0

    def _override_chain(self) -> Optional[List[Dict[str, str]]]:
        """用户指定总模型时，所有角色都用它。"""
        if not self._override_model:
            return None
        provider = self._override_provider
        if not provider:
            # 从配置里反查该 model 属于哪个 provider
            for p in self._config.providers:
                for m in p.models:
                    if m.id == self._override_model:
                        provider = p.name
                        break
                if provider:
                    break
        if not provider:
            return None
        return [{"provider": provider, "model": self._override_model}]

    def resolve(self, task_type: str) -> List[Dict[str, str]]:
        """返回 [{provider, model}, ...] 候选链。

        优先级（数字越小越优先）：
            1. ModelRouter override_model    ← 前端选具体模型全局覆盖
            2. user_routing per_role[role]
            3. user_routing simple override_model
            4. Model Registry role routing   ← 前端配置中心改即生效
            5. yaml agent_routing[role]
            6. 兜底：第一个可用模型
        """
        # ── 1. ModelRouter override_model（显式全局覆盖，最高优先级） ──
        override = self._override_chain()
        if override:
            return override

        # ── 2. user_routing per_role ──
        ur = self._user_routing
        if ur is not None and getattr(ur, "mode", "") == "per_role":
            ref = ur.per_role.get(task_type)
            if ref is not None and ref.provider and ref.model:
                return [{"provider": ref.provider, "model": ref.model}]

        # ── 3. user_routing simple ──
        if ur is not None and getattr(ur, "mode", "") == "simple":
            om = (ur.override_model or "").strip()
            if om:
                prov = self._find_provider_for_model(om)
                if prov:
                    return [{"provider": prov, "model": om}]

        # ── 4. Model Registry role routing（前端配置中心改即生效） ──
        try:
            from backend.core.model_registry.registry import get_registry
            reg = get_registry()
            route = reg.roles.get(task_type)
            if route and route.primary:
                m = reg.models.get(route.primary)
                if m:
                    chain: List[Dict[str, str]] = [
                        {"provider": m.provider_id, "model": m.id},
                    ]
                    if route.fallback:
                        fb = reg.models.get(route.fallback)
                        if fb:
                            chain.append(
                                {"provider": fb.provider_id, "model": fb.id}
                            )
                    return chain
        except Exception as exc:
            print(f"[model-router] registry lookup failed: {exc}",
                  flush=True)

        # ── 5. yaml agent_routing ──
        chain = self._config.routing_chain(task_type)
        if not chain:
            # ── 6. 兜底 ──
            for p in self._config.providers:
                for mm in p.models:
                    return [{"provider": p.name, "model": mm.id}]
            raise RuntimeError("no model available; check llm_providers.yaml")
        return [r.to_dict() for r in chain]


    async def chat(
        self,
        *,
        gateway: Any,
        task_type: str,
        provider: str = "",
        messages: List[dict],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        candidates = self.resolve(task_type)
        last_error: Optional[str] = None

        for i, cand in enumerate(candidates):
            self.call_count += 1
            model = cand["model"]
            prov = cand["provider"]
            t0 = time.perf_counter()
            try:
                response = await gateway.chat(
                    provider=prov,
                    model=model,
                    messages=messages,
                    _role=task_type,
                    **kwargs,
                )
                latency = (time.perf_counter() - t0) * 1000
                in_tok = estimate_messages(messages)
                out_tok = estimate_tokens(str(response))
                # 记录已由 gateway 统一完成（避免双记）
                if i > 0:
                    self.fallback_count += 1
                return {
                    "provider": prov,
                    "model": model,
                    "response": response,
                    "fallback_used": i > 0,
                    "attempts": i + 1,
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "latency_ms": latency,
                }
            except Exception as error:
                latency = (time.perf_counter() - t0) * 1000
                last_error = (
                    f"{prov}/{model}: "
                    f"{type(error).__name__}: {error}"
                )
                # 记录已由 gateway 统一完成（避免双记）
                print(
                    f"[model-router] task={task_type} "
                    f"{prov}/{model} failed: {error}",
                    flush=True,
                )
                continue

        raise RuntimeError(
            f"all candidate models failed for task={task_type}; "
            f"last_error={last_error}"
        )

    def stream_chat(
        self,
        *,
        gateway: Any,
        task_type: str,
        provider: str = "",
        messages: List[dict],
        **kwargs: Any,
    ):
        """流式：返回 async iterator，逐 token yield。"""
        candidates = self.resolve(task_type)
        tracker = get_tracker()

        async def _gen():
            last_error: Optional[str] = None
            for i, cand in enumerate(candidates):
                self.call_count += 1
                model = cand["model"]
                prov = cand["provider"]
                t0 = time.perf_counter()
                collected = []
                try:
                    stream = gateway.stream_chat(
                        provider=prov, model=model,
                        messages=messages,
                        _role=task_type,
                        **kwargs,
                    )
                    async for chunk in stream:
                        text = chunk if isinstance(chunk, str) else str(chunk)
                        collected.append(text)
                        yield text
                    # 记录已由 gateway 统一完成（避免双记）
                    if i > 0:
                        self.fallback_count += 1
                    return
                except Exception as error:
                    last_error = f"{prov}/{model}: {type(error).__name__}: {error}"
                    print(
                        f"[model-router] stream task={task_type} "
                        f"{prov}/{model} failed: {error}",
                        flush=True,
                    )
                    continue
            raise RuntimeError(
                f"all candidates failed for stream task={task_type}; "
                f"last_error={last_error}"
            )

        return _gen()

    def ready(self) -> bool:
        return bool(self._config.providers)
