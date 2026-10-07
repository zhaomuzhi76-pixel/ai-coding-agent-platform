"""Ollama 文本向量客户端（同步）。
职责：调 /api/embed（新）或 /api/embeddings（旧）拿向量。
不做缓存、不做并发、不持有状态。
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Sequence

from backend.core.model_registry.embedding_resolver import (
    resolve_embedding_model)
from backend.config.constants.endpoints import OLLAMA_URL

DEFAULT_ENDPOINT = OLLAMA_URL
DEFAULT_MODEL = (
    os.environ.get("RAG_OLLAMA_EMBED_MODEL")
    or "qwen3-embedding:4b"
)
DEFAULT_TIMEOUT = 120.0

# 模型驻留时长（秒），任务期间保持，任务结束自动卸载
_KEEP_ALIVE = int(os.environ.get("RAG_OLLAMA_KEEP_ALIVE", "600"))

# GPU 优化参数（防止显存溢出到 CPU）
_NUM_CTX = int(os.environ.get("RAG_OLLAMA_NUM_CTX", "512"))   # 4096→512 省 476MB
_NUM_GPU = int(os.environ.get("RAG_OLLAMA_NUM_GPU", "99"))    # 强制全 GPU
_NUM_THREAD = int(os.environ.get("RAG_OLLAMA_NUM_THREAD", "0"))


class OllamaEmbedClient:
    def __init__(self, endpoint: str = DEFAULT_ENDPOINT,
                 model: str = DEFAULT_MODEL,
                 timeout: float = DEFAULT_TIMEOUT) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _opts(self) -> dict:
        return {"num_ctx": _NUM_CTX, "num_gpu": _NUM_GPU,
                "num_thread": _NUM_THREAD}

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """批量优先 /api/embed，失败回退 /api/embeddings。"""
        texts = [str(t) for t in texts]
        if not texts:
            return []

        # 优先批量接口 /api/embed
        try:
            return self._embed_batch(texts)
        except Exception as e:
            print(f"[ollama_embed] /api/embed 失败，回退单条: {e}",
                  flush=True)

        # 回退单条
        return [self._embed_one(t) for t in texts]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({
            "model": self.model,
            "input": texts,
            "keep_alive": _KEEP_ALIVE,
            "options": self._opts(),
        }).encode()
        req = urllib.request.Request(
            f"{self.endpoint}/api/embed", data=body,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read())
        return data.get("embeddings") or []

    def _embed_one(self, text: str) -> list[float]:
        body = json.dumps({
            "model": self.model,
            "prompt": text,
            "keep_alive": _KEEP_ALIVE,
            "options": self._opts(),
        }).encode()
        req = urllib.request.Request(
            f"{self.endpoint}/api/embeddings", data=body,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read())
        return data.get("embedding") or []

    # 兼容旧调用
    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        return self.embed(texts)


__all__ = ["OllamaEmbedClient", "DEFAULT_ENDPOINT", "DEFAULT_MODEL"]


def make_embed_fn(model: str = "", endpoint: str = "",
                  timeout: float = DEFAULT_TIMEOUT):
    """工厂：返回可调用的 embed_fn(texts) -> list[list[float]]。
    兼容多种调用方式：
      1. make_embed_fn()                   # 用默认模型
      2. make_embed_fn("qwen3-embedding:4b")
      3. make_embed_fn(model="...", endpoint="...")
    """
    client = OllamaEmbedClient(
        endpoint=(endpoint or DEFAULT_ENDPOINT),
        model=(model or DEFAULT_MODEL),
        timeout=timeout,
    )
    # 返回的对象既是 client，也可直接调用
    return client.embed


def unload_model(model: str = "", endpoint: str = "") -> bool:
    """[GPU_RELEASE] 显式卸载 Ollama 模型，释放显存。"""
    import urllib.request, json as _j
    m = model or DEFAULT_MODEL
    url = (endpoint or DEFAULT_ENDPOINT).rstrip("/") + "/api/generate"
    try:
        body = _j.dumps({"model": m, "keep_alive": 0}).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10).read()
        return True
    except Exception:
        return False
