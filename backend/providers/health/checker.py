"""Provider health checker.

工业级契约：
  - ollama             → 真实探测 /api/tags（3s 超时）
  - dashscope          → 真实探测 /models（5s 超时）
  - anthropic          → 真实探测 /v1/models（5s 超时）
  - openai_compatible  → 真实探测 /models（5s 超时）
  - 其它               → 静态检查（base_url + api_key 非空）
  - check_all          → 并发探测；单失败不拖累其它
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from backend.providers.health.cache import HealthCache
from backend.providers.health.record import HealthRecord
from backend.providers.health.remote_probe import probe_remote


class ProviderHealthChecker:
    VERSION = "1.1"

    def __init__(self, cache: Optional[HealthCache] = None) -> None:
        self._cache = cache or HealthCache()
        self._specs: Dict[str, Dict[str, Any]] = {}

    @property
    def cache(self) -> HealthCache:
        return self._cache

    def register(
        self, name: str, ptype: str, base_url: str, api_key: str,
    ) -> None:
        if not name.strip():
            raise ValueError("provider name required")
        self._specs[name] = {
            "type": ptype.strip(),
            "base_url": base_url.strip(),
            "api_key": api_key.strip(),
        }

    async def check_one(self, provider: str) -> HealthRecord:
        spec = self._specs.get(provider)
        if spec is None:
            return HealthRecord(
                provider=provider, status="unknown",
                error="provider not registered",
            )
        ptype = spec["type"]
        # 远程 provider → 真实探测（5s）
        if ptype in ("dashscope", "anthropic", "openai_compatible"):
            return await self._remote_probe(provider, spec)
        # ollama → 真实探测（3s）
        if ptype == "ollama":
            return await self._ollama_probe(provider, spec)
        # 其它 → 静态检查
        return self._static_check(provider, spec)

    def _static_check(
        self, provider: str, spec: Dict[str, Any],
    ) -> HealthRecord:
        base_url = spec.get("base_url", "")
        api_key = spec.get("api_key", "")
        if not base_url:
            return self._cache.update_on_failure(provider, "base_url missing")
        if spec["type"] in ("dashscope", "anthropic", "openai_compatible"):
            if not api_key:
                return self._cache.update_on_failure(provider, "api_key missing")
        rec = HealthRecord(provider=provider, status="healthy")
        self._cache.put(rec)
        return rec

    async def _remote_probe(
        self, provider: str, spec: Dict[str, Any],
    ) -> HealthRecord:
        """真实探测远程 provider。"""
        ok, err, latency = await probe_remote(spec)
        if ok:
            self._cache.update_on_success(provider, latency)
            rec = self._cache.get(provider)
            return rec if rec else HealthRecord(
                provider=provider, status="healthy",
                latency_ms=latency,
            )
        return self._cache.update_on_failure(provider, err)

    async def _ollama_probe(
        self, provider: str, spec: Dict[str, Any],
    ) -> HealthRecord:
        base_url = spec.get("base_url", "").rstrip("/")
        if not base_url:
            return self._cache.update_on_failure(provider, "base_url missing")
        start = time.perf_counter()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get(f"{base_url}/api/tags")
                r.raise_for_status()
            latency = (time.perf_counter() - start) * 1000
            self._cache.update_on_success(provider, latency)
            rec = self._cache.get(provider)
            return rec if rec else HealthRecord(
                provider=provider, status="healthy",
            )
        except Exception as exc:
            return self._cache.update_on_failure(
                provider, f"{type(exc).__name__}: {exc}",
            )

    async def check_all(self) -> List[HealthRecord]:
        """并发探测；单个失败不影响其它。"""
        import asyncio
        names = list(self._specs)
        tasks = [self.check_one(n) for n in names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: List[HealthRecord] = []
        for n, r in zip(names, results):
            if isinstance(r, HealthRecord):
                out.append(r)
            else:
                out.append(HealthRecord(
                    provider=n, status="unhealthy",
                    error=f"probe crashed: {r}",
                ))
        return out

    def cached(self, provider: str) -> Optional[HealthRecord]:
        return self._cache.get(provider)

    def is_healthy(self, provider: str) -> Optional[bool]:
        rec = self._cache.get(provider)
        if rec is None:
            return None
        return rec.is_healthy

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "registered": list(self._specs.keys()),
            "cache": self._cache.dump(),
        }


__all__ = ["ProviderHealthChecker"]
