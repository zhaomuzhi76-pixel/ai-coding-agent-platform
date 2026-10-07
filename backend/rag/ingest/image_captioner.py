"""图片 caption 生成器：调 Ollama VLM 生成简短中文描述。

职责：
  - 输入图片 bytes → 输出 caption 字符串
  - 单例 HTTP 客户端；env 控制开关与模型
不做：
  - 不做 OCR、不做向量化
"""
from __future__ import annotations
import base64
import json
import logging
import os
import urllib.request
from typing import List, Optional

logger = logging.getLogger(__name__)

_ENV_ENABLED = "RAG_IMG_CAPTION_ENABLED"
_ENV_MODEL = "RAG_IMG_CAPTION_MODEL"
_ENV_URL = "RAG_OLLAMA_URL"
_DEFAULT_MODEL = "qwen3.5:4b"
_DEFAULT_URL = "http://127.0.0.1:11434"
_PROMPT = "用一句话（不超过20字）描述这张中药材图片的主体。只输出描述，不要任何前缀。"
_TIMEOUT = 60


def enabled() -> bool:
    return os.environ.get(_ENV_ENABLED, "0") == "1"


def model() -> str:
    return os.environ.get(_ENV_MODEL, _DEFAULT_MODEL)


def _url() -> str:
    return os.environ.get(_ENV_URL, _DEFAULT_URL).rstrip("/")


def caption_png(image_bytes: bytes, *,
                model_name: Optional[str] = None,
                timeout: int = _TIMEOUT) -> str:
    """同步生成 caption。失败返回空串（不抛）。"""
    if not image_bytes:
        return ""
    b64 = base64.b64encode(image_bytes).decode("ascii")
    body = {
        "model": model_name or model(),
        "prompt": _PROMPT,
        "images": [b64],
        "stream": False,
        "keep_alive": "30s",   # 生成完尽快释放显存
        "options": {"num_predict": 40, "temperature": 0.1},
    }
    req = urllib.request.Request(
        _url() + "/api/generate",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        return (data.get("response") or "").strip()[:80]
    except Exception as e:
        logger.debug("[caption] failed: %r", e)
        return ""


def caption_batch(images: List[bytes], *, max_n: int = 0) -> List[str]:
    """批量；max_n=0 全部，>0 只处理前 N 张。"""
    if not images:
        return []
    n = len(images) if max_n <= 0 else min(max_n, len(images))
    return [caption_png(b) for b in images[:n]]


__all__ = ["enabled", "model", "caption_png", "caption_batch"]
