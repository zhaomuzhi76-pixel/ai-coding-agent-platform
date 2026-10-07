"""Agent Loop Gateway：把同步 OllamaClient 包装为 async gateway。
职责：提供 chat(provider, messages, model) -> str 异步接口，
      内部通过 asyncio.to_thread 调用同步 OllamaClient，避免阻塞事件循环。
不解析 prompt、不做工具调用、不管 session。
与 providers/runtime/ollama_client.py 边界：
  那层是同步 HTTP 客户端；本层只做"同步→异步"适配 + 消息格式收敛。
"""
from __future__ import annotations
import asyncio
from typing import Any, Mapping, Optional, Sequence

import os as _os_g  # [ENV]

DEFAULT_TIMEOUT = 60.0
DEFAULT_SYSTEM = "你是多领域 AI 助手，用中文简洁回答。"
# [ENV] 本地 Ollama 兜底模型（当 role routing 给的模型本地没有时用）
ENV_DEFAULT_MODEL = _os_g.environ.get(
    "RAG_OLLAMA_DEFAULT_MODEL", "qwen3:8b")

def _normalize(messages: Sequence[Mapping[str, Any]]) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if not isinstance(m, Mapping):
            continue
        role = str(m.get("role", "user"))
        if role not in ("system", "user", "assistant"):
            role = "user"
        content = str(m.get("content", ""))
        out.append({"role": role, "content": content})
    return out

class OllamaGateway:
    """同步 OllamaClient → async gateway。"""
    def __init__(self, client: Any, *, timeout: float = DEFAULT_TIMEOUT,
                 default_model: str = "") -> None:
        if client is None:
            raise ValueError("client required")
        if not callable(getattr(client, "chat", None)):
            raise TypeError("client 缺 chat()")
        self._client = client
        self._timeout = timeout
        self._default_model = default_model

    def _local_models(self) -> set:
        """拿 Ollama 本地已装模型集合。失败返回空集。"""
        try:
            ms = self._client.list_models()
            out = set()
            for m in (ms or []):
                s = str(m).strip()
                if s:
                    out.add(s)
                    # 归一化：去 :latest
                    if s.endswith(":latest"):
                        out.add(s[:-7])
            return out
        except Exception:
            return set()

    def _resolve_auto_model(self) -> str:
        """[AUTO] 从 ROLE ROUTING 拿候选，但**只认 Ollama 本地已装**。
        候选顺序：complex > intent > plan > code > review > _default_model > ENV_DEFAULT。
        找不到 → 用本地第一个模型；本地空 → 用 env 默认（可能还会 404）。
        """
        local = self._local_models()

        # 候选列表
        candidates: list = []
        try:
            from backend.core.model_registry.registry import get_registry
            reg = get_registry()
            for role in ("complex", "intent", "plan", "code", "review"):
                route = reg.get_role_route(role)
                p = getattr(route, "primary", "") if route else ""
                if p and str(p).strip():
                    candidates.append(str(p).strip())
        except Exception:
            pass
        if self._default_model:
            candidates.append(self._default_model.strip())
        if ENV_DEFAULT_MODEL:
            candidates.append(ENV_DEFAULT_MODEL.strip())

        # 逐个匹配本地
        for c in candidates:
            if not c:
                continue
            if c in local:
                return c
            # 模糊：qwen3:8b vs qwen3:8b:latest
            for m in local:
                if m == c or m.startswith(c + ":") or c == m.split(":")[0]:
                    return m

        # 本地一个都匹配不上 → 用本地第一个（救命）
        if local:
            for m in sorted(local):
                if "embedding" not in m.lower() and "reranker" not in m.lower():
                    return m
            return sorted(local)[0]

        return self._default_model or ENV_DEFAULT_MODEL or ""

    async def chat(self, provider: str, messages: Sequence[Mapping[str, Any]],
                   model: str = "") -> str:
        # [AUTO] "__auto__" 或空 → 从 role routing 拿
        raw = (model or "").strip()
        if raw == "__auto__" or not raw:
            model_id = self._resolve_auto_model().strip()
        else:
            model_id = raw
        # [FALLBACK] 最终校验：本地没有就换本地第一个（防 404）
        local = self._local_models()
        if local and model_id not in local:
            # 模糊匹配
            match = None
            for m in local:
                if m == model_id or m.startswith(model_id + ":") \
                        or model_id == m.split(":")[0]:
                    match = m
                    break
            if match is None:
                # 换本地第一个非 embedding/reranker 的
                for m in sorted(local):
                    if "embedding" not in m.lower() \
                            and "reranker" not in m.lower():
                        match = m
                        break
                if match is None:
                    match = sorted(local)[0]
                import logging
                logging.getLogger(__name__).warning(
                    "[gateway] 模型 %r 本地不存在，自动回退到 %r",
                    model_id, match)
            model_id = match

        if not model_id:
            raise ValueError("model required (provider=%s)" % provider)
        msgs = _normalize(messages)
        if not msgs:
            raise ValueError("messages required")

        def _call():
            return self._client.chat(model=model_id, messages=msgs)

        result = await asyncio.wait_for(
            asyncio.to_thread(_call), timeout=self._timeout)
        text = getattr(result, "text", None)
        if text is None:
            return str(result)
        return str(text)

class EchoGateway:
    """无 LLM 时的兜底：直接把最后一条 user content 回显为 JSON。"""
    async def chat(self, provider: str, messages: Sequence[Mapping[str, Any]],
                   model: str = "") -> str:
        last = ""
        for m in messages:
            if isinstance(m, Mapping) and m.get("role") == "user":
                last = str(m.get("content", ""))
        import json
        return json.dumps({"thought": "echo", "done": True,
                           "answer": last[:200]}, ensure_ascii=False)

def make_gateway(client: Optional[Any] = None, *,
                 timeout: float = DEFAULT_TIMEOUT,
                 default_model: str = "") -> Any:
    if client is None:
        return EchoGateway()
    return OllamaGateway(client, timeout=timeout, default_model=default_model)

__all__ = ["OllamaGateway", "EchoGateway", "make_gateway"]
