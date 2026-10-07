from __future__ import annotations
from backend.core.observability.silent import swallow

import time
from typing import Any, AsyncIterator

from backend.application.provider_gateway.contracts import (
    ApplicationProviderGatewayProtocol,
    ApplicationProviderRuntimeProtocol,
)


def _record_call(
    *,
    provider: str,
    model: str,
    messages: list,
    response: str = "",
    latency_ms: float,
    role: str = "",
    success: bool = True,
    error: str = "",
) -> None:
    """统一记录（全项目唯一记录点）。"""
    try:
        from backend.providers.cost import (
            get_tracker, estimate_messages, estimate_tokens,
        )
        in_tok = estimate_messages(messages)
        out_tok = estimate_tokens(response) if success else 0
        get_tracker().record(
            provider=str(provider or ""),
            model=str(model or ""),
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=float(latency_ms),
            role=role,
            success=success,
            error=error,
        )
    except Exception as e:
        swallow("application.provider_gateway.gateway:42", e)


class ApplicationProviderGateway(
    ApplicationProviderGatewayProtocol,
):
    """
    Application-side provider execution boundary.

    Depends only on the stable provider runtime protocol.
    """

    VERSION = "2.1"

    def __init__(
        self,
        runtime: ApplicationProviderRuntimeProtocol,
    ) -> None:
        if runtime is None:
            raise ValueError(
                "provider runtime required"
            )

        if not isinstance(
            runtime,
            ApplicationProviderRuntimeProtocol,
        ):
            raise TypeError(
                "provider runtime must implement "
                "ApplicationProviderRuntimeProtocol"
            )

        if not runtime.ready():
            raise RuntimeError(
                "provider runtime not ready"
            )

        self.runtime = runtime
        self.execution_count = 0

    async def chat(
        self,
        provider: str | None,
        messages: list[dict],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        self.execution_count += 1
        role = str(kwargs.pop("_role", "") or "")
        t0 = time.perf_counter()
        try:
            response = await self.runtime.chat(
                provider,
                messages,
                model,
                **kwargs,
            )
        except Exception as exc:
            _record_call(
                provider=str(provider or ""),
                model=str(model or ""),
                messages=messages,
                latency_ms=(time.perf_counter() - t0) * 1000,
                role=role,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )
            raise
        _record_call(
            provider=str(provider or ""),
            model=str(model or ""),
            messages=messages,
            response=str(response),
            latency_ms=(time.perf_counter() - t0) * 1000,
            role=role,
            success=True,
        )
        return response

    def stream_chat(
        self,
        provider: str | None,
        messages: list[dict],
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self.execution_count += 1
        role = str(kwargs.pop("_role", "") or "")
        inner = self.runtime.stream_chat(
            provider,
            messages,
            model,
            **kwargs,
        )

        async def _gen() -> AsyncIterator[str]:
            t0 = time.perf_counter()
            collected: list[str] = []
            try:
                async for chunk in inner:
                    text = chunk if isinstance(chunk, str) else str(chunk)
                    collected.append(text)
                    yield text
            except Exception as exc:
                _record_call(
                    provider=str(provider or ""),
                    model=str(model or ""),
                    messages=messages,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    role=role,
                    success=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
                raise
            _record_call(
                provider=str(provider or ""),
                model=str(model or ""),
                messages=messages,
                response="".join(collected),
                latency_ms=(time.perf_counter() - t0) * 1000,
                role=role,
                success=True,
            )

        return _gen()

    async def embedding(
        self,
        provider: str | None,
        texts: list[str],
        model: str | None = None,
        **kwargs: Any,
    ) -> list[list[float]]:
        self.execution_count += 1

        return await self.runtime.embedding(
            provider,
            texts,
            model,
            **kwargs,
        )

    def ready(self) -> bool:
        return self.runtime.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "execution_count": self.execution_count,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationProviderGateway",
]
