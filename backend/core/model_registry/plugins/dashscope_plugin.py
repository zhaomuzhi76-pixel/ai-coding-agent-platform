"""阿里云百炼 DashScope Provider 插件

协议：OpenAI 兼容（/compatible-mode/v1 端点走 /models）
- 探测：GET {base_url}/models，带 Authorization: Bearer {api_key}
- 兜底：401/403 视为可达（key 无效但服务在）
"""
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


class DashScopePlugin(BaseProviderPlugin):
    def _compat_base(self) -> str:
        """保证走 OpenAI 兼容端点（/compatible-mode/v1）"""
        base = (self.config.base_url or "").rstrip("/")
        # 若用户填的是根域名，自动补 compatible-mode/v1
        if base in ("https://dashscope.aliyuncs.com",
                    "https://dashscope.aliyuncs.com/"):
            return base + "/compatible-mode/v1"
        return base

    def _headers(self):
        h = {}
        if self.config.api_key:
            h["Authorization"] = f"Bearer {self.config.api_key}"
        return h

    def test_connection(self) -> bool:
        if _offline():
            return bool(self.config.api_key)
        if not self.config.api_key:
            return False
        try:
            url = self._compat_base() + "/models"
            _http_json(url, headers=self._headers())
            return True
        except urllib.error.HTTPError as e:
            # 401/403 说明端点可达、协议对，只是 key 问题 → 视为可达
            return e.code in (200, 401, 403)
        except json.JSONDecodeError:
            # 端点返回非 JSON（错误页），但至少说明域名可达
            return False
        except Exception:
            return False

    def fetch_models(self) -> List[ModelInfo]:
        if _offline() or not self.config.api_key:
            return self._fallback_models()
        try:
            url = self._compat_base() + "/models"
            data = _http_json(url, headers=self._headers())
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
        return self._fallback_models()

    def _fallback_models(self) -> List[ModelInfo]:
        """静态兜底：常见百炼模型清单"""
        return [
            ModelInfo(id="qwen-max", provider_id=self.config.id,
                      display_name="Qwen Max", context_window=131072,
                      cost_per_1k=0.02),
            ModelInfo(id="qwen-coder-plus", provider_id=self.config.id,
                      display_name="Qwen Coder Plus", context_window=131072,
                      cost_per_1k=0.01),
            ModelInfo(id="qwen-plus", provider_id=self.config.id,
                      display_name="Qwen Plus", context_window=131072,
                      cost_per_1k=0.004),
        ]

    def generate(self, model_id: str, prompt: str, **kwargs) -> str:
        return f"[dashscope/{model_id}] {prompt}"
