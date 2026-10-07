"""Ollama LLM 客户端。职责：HTTP 调 /api/chat，返回文本。
不做路由、不做选择、不持有状态。"""
from __future__ import annotations
from backend.config.constants.endpoints import (
    OLLAMA_URL,
)

import json
import urllib.request
from dataclasses import dataclass
from typing import Optional

DEFAULT_ENDPOINT = OLLAMA_URL
DEFAULT_TIMEOUT = 180.0

@dataclass(frozen=True)
class OllamaChatResult:
    text: str
    model: str
    done: bool

class OllamaClient:
    def __init__(self, endpoint: str = DEFAULT_ENDPOINT, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def chat(self, *, model: str, messages: list[dict],
             images_b64: Optional[list[str]] = None) -> OllamaChatResult:
        payload_messages = [dict(m) for m in messages]
        if images_b64:
            if not payload_messages:
                payload_messages = [{"role": "user", "content": "", "images": images_b64}]
            else:
                payload_messages[-1]["images"] = images_b64
        # [TEMP] 低随机（env RAG_LLM_TEMPERATURE · 默认 0.1）
        import os as _os_temp
        try:
            _temperature = float(_os_temp.environ.get(
                "RAG_LLM_TEMPERATURE", "0.1"))
        except (TypeError, ValueError):
            _temperature = 0.1
        body = json.dumps({
            "model": model, "messages": payload_messages, "stream": False,
            "options": {"temperature": _temperature},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.endpoint}/api/chat", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        msg = data.get("message") or {}
        return OllamaChatResult(text=str(msg.get("content", "")),
                                model=str(data.get("model", model)),
                                done=bool(data.get("done", True)))

    def list_models(self) -> list[str]:
        req = urllib.request.Request(f"{self.endpoint}/api/tags")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in data.get("models", [])]
