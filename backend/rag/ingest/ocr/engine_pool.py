"""多语言 OCR 引擎池。职责：按语言缓存 PaddleOcrEngine 单例。
支持：ch（简体+英文混合）、chinese_cht（繁体）、en、japan、korean。
懒加载：每种语言第一次用时初始化，后续复用。
线程安全。
"""
from __future__ import annotations
import threading
from typing import Optional

from backend.rag.ingest.ocr.paddle_engine import (
    PaddleOcrEngine, _SUPPORTED_LANG)

DEFAULT_LANG = "chinese_cht"  # 默认繁体（古籍场景）

# UI 下拉可选的常用语言（值 = lang, 显示名）
LANG_CHOICES = (
    ("chinese_cht", "繁体中文（古籍）"),
    ("ch", "简体中文 + 英文混合"),
    ("en", "英文"),
    ("japan", "日文"),
)

def _check_lang(lang: str) -> str:
    if lang not in _SUPPORTED_LANG:
        raise ValueError(f"不支持的语言: {lang!r}，支持: {_SUPPORTED_LANG}")
    return lang

class OcrEnginePool:
    def __init__(self, *, use_gpu: bool = False) -> None:
        self._engines: dict[str, PaddleOcrEngine] = {}
        self._lock = threading.Lock()
        self._use_gpu = use_gpu

    def get(self, lang: str = DEFAULT_LANG) -> PaddleOcrEngine:
        lang = _check_lang(lang)
        if lang in self._engines:
            return self._engines[lang]
        with self._lock:
            if lang in self._engines:
                return self._engines[lang]
            e = PaddleOcrEngine(lang=lang, use_gpu=self._use_gpu)
            self._engines[lang] = e
            return e

    def ready_languages(self) -> list:
        return sorted(self._engines.keys())

    def clear(self) -> None:
        with self._lock:
            self._engines.clear()

_DEFAULT: Optional[OcrEnginePool] = None

def get_default_pool() -> OcrEnginePool:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = OcrEnginePool()
    return _DEFAULT

def set_default_pool(p: Optional[OcrEnginePool]) -> None:
    global _DEFAULT
    _DEFAULT = p

__all__ = ["OcrEnginePool", "get_default_pool", "set_default_pool",
           "LANG_CHOICES", "DEFAULT_LANG"]
