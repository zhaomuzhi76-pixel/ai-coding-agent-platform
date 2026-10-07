"""LLM 桥。职责：把 prompt 交给 LLM（Ollama），返回文本。
不做图片、不做路由、不组装响应。"""
from __future__ import annotations
from typing import Optional
from backend.providers.runtime.ollama_client import OllamaClient

DEFAULT_SYSTEM = "你是中文 AI 助手，回答简洁、准确。"

class LlmBridge:
    def __init__(self, client: OllamaClient,
                 system_prompt: str = DEFAULT_SYSTEM) -> None:
        self._client = client
        self._system = system_prompt

    def generate_text(self, model_id: str, prompt: str,
                 images_b64: Optional[list[str]] = None) -> str:
        msgs: list[dict] = []
        if self._system:
            msgs.append({"role": "system", "content": self._system})
        msgs.append({"role": "user", "content": prompt})
        r = self._client.chat(model=model_id, messages=msgs,
                              images_b64=images_b64)
        return r.text
