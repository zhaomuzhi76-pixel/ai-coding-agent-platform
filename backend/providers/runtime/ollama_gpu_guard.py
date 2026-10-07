"""Ollama GPU 守卫：调 embed/chat 前先抢 GPU 锁，
用完让位给 OCR（若 OCR 请求）。
独立插件，不改 ollama_embed.py 核心。
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


def acquire_before_ollama(need_mb: int = 4000) -> bool:
    """Ollama 调用前：抢锁（会驱逐 reranker；但若 OCR 持锁则等它让位）。
    返回 True 表示可以调 Ollama。"""
    try:
        from backend.rag.ingest.ocr.gpu_lock import acquire, holder
        # 若 OCR 正在跑，等它完成（不抢）
        if holder() == "ocr":
            logger.info("[ollama-guard] OCR 运行中，Ollama 暂缓")
            return False
        return acquire("ollama", need_mb=need_mb, wait_s=15)
    except Exception as e:
        logger.warning("[ollama-guard] 抢锁失败: %r", e)
        return True  # 降级：直接调，不阻止


def release_after_ollama() -> None:
    try:
        from backend.rag.ingest.ocr.gpu_lock import release
        release("ollama")
    except Exception:
        pass


__all__ = ["acquire_before_ollama", "release_after_ollama"]
