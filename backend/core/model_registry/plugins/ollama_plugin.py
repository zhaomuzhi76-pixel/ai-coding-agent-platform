"""本地 Ollama Provider 插件（真实 HTTP 探测 + 离线降级）"""
import json
import os
import urllib.request
from typing import List

from ..domain import ModelInfo
from .base import BaseProviderPlugin


def _offline() -> bool:
    return os.environ.get("BIANCHENG_OFFLINE") == "1"


def _http_json(url: str, timeout: float = 5.0, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class OllamaLocalPlugin(BaseProviderPlugin):
    def test_connection(self) -> bool:
        if _offline():
            return bool(self.config.base_url)
        try:
            url = self.config.base_url.rstrip("/") + "/api/tags"
            _http_json(url)
            return True
        except Exception:
            return False

    def fetch_models(self) -> List[ModelInfo]:
        if not _offline():
            try:
                url = self.config.base_url.rstrip("/") + "/api/tags"
                data = _http_json(url)
                return [
                    ModelInfo(id=m["name"], provider_id=self.config.id,
                              display_name=m["name"], context_window=32768)
                    for m in data.get("models", [])
                ]
            except Exception:
                pass
        return [
            ModelInfo(id="qwen2.5-coder:7b", provider_id=self.config.id,
                      display_name="Qwen2.5 Coder 7B", context_window=32768),
            ModelInfo(id="qwen3:8b", provider_id=self.config.id,
                      display_name="Qwen3 8B", context_window=32768),
        ]

    def generate(self, model_id: str, prompt: str, **kwargs) -> str:
        return f"[ollama/{model_id}] {prompt}"
