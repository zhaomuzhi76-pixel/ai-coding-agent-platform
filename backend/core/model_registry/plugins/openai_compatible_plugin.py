"""通用 OpenAI 兼容 Provider 插件（覆盖 vLLM/OpenAI/Anthropic/DeepSeek/智谱/月之暗面/Gemini/硅基流动/OpenRouter 等）"""
import json
import os
import urllib.error
import urllib.request
from typing import List

from ..domain import ModelInfo
from .base import BaseProviderPlugin


def _offline() -> bool:
    return os.environ.get("BIANCHENG_OFFLINE") == "1"


def _http_json(url: str, timeout: float = 8.0, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class OpenAICompatiblePlugin(BaseProviderPlugin):
    def test_connection(self) -> bool:
        if not self.config.base_url:
            return False
        if _offline():
            return True
        if not self.config.api_key:
            # 本地 vLLM/LM Studio 可能无 key；云端必须有
            if "127.0.0.1" not in self.config.base_url and "localhost" not in self.config.base_url:
                return False
        try:
            url = self.config.base_url.rstrip("/") + "/models"
            h = {}
            if self.config.api_key:
                h["Authorization"] = f"Bearer {self.config.api_key}"
            _http_json(url, headers=h)
            return True
        except urllib.error.HTTPError as e:
            # 401/403 说明 API 可达但 key 无效；仍视为"可达"
            return e.code in (200, 401, 403)
        except Exception:
            return False

    def fetch_models(self) -> List[ModelInfo]:
        if not _offline() and self.config.base_url:
            try:
                url = self.config.base_url.rstrip("/") + "/models"
                h = {}
                if self.config.api_key:
                    h["Authorization"] = f"Bearer {self.config.api_key}"
                data = _http_json(url, headers=h)
                items = data.get("data") or data.get("models") or []
                out = []
                for m in items:
                    mid = m.get("id") or m.get("name")
                    if mid:
                        out.append(ModelInfo(
                            id=mid, provider_id=self.config.id,
                            display_name=mid, context_window=131072))
                if out:
                    return out
            except Exception:
                pass
        # 离线 / 探测失败 → 无预置模型（由用户手动指定）
        return []

    def generate(self, model_id: str, prompt: str, **kwargs) -> str:
        return f"[{self.config.id}/{model_id}] {prompt}"
