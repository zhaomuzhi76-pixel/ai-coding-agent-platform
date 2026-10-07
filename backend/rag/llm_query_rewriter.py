"""LLM 查询改写（症状/口语 → 药名列表）。

职责：
  - 判断是否需要改写（长 query / 症状词）
  - 调 Ollama LLM 输出药名 CSV
  - 缓存改写结果（LRU，同 query 只算一次）

不做：
  - 不检索（orchestrator 管）
  - 不编码（embedder 管）

配置（env）：
  RAG_QUERY_REWRITE_ENABLED=1  打开（默认关，保守）
  RAG_QUERY_REWRITE_MODEL      LLM 模型（默认 gemma3:latest）
  RAG_QUERY_REWRITE_TIMEOUT    超时秒（默认 30）
"""
from __future__ import annotations
import json
import logging
import os
import re
import threading
import urllib.request
from collections import OrderedDict
from typing import List, Optional

logger = logging.getLogger(__name__)

_ENV_ENABLED = "RAG_QUERY_REWRITE_ENABLED"
_ENV_MODEL = "RAG_QUERY_REWRITE_MODEL"
_ENV_URL = "RAG_QUERY_REWRITE_OLLAMA_URL"
_ENV_TIMEOUT = "RAG_QUERY_REWRITE_TIMEOUT"
from backend.rag.plugins import model_resolver as _resolver

_DEFAULT_MODEL = _resolver.default_chat_model() or ""

_DEFAULT_URL = "http://127.0.0.1:11434"
_DEFAULT_TIMEOUT = 30

# 触发改写的症状/口语词
_SYMPTOM_KW = (
    "治", "治什么", "什么药", "吃什么", "用什么",
    "可以治", "可以吃", "缓解", "改善",
    "症状", "表现", "症见",
    "感冒", "咳嗽", "头痛", "发热", "腰痛", "肚痛", "腹痛",
    "补气", "补血", "活血", "清热", "解毒", "化痰", "止咳",
    "明目", "安神", "健脾", "养胃", "滋阴", "壮阳",
)

_PROMPT = """你是中医专家。请把用户的查询改写为**不超过 8 个最相关的药材名**（用中文逗号分隔），只输出药名，不要解释。

示例：
用户：治咳嗽的中药
输出：桑叶,菊花,杏仁,牛蒡子,薄荷,桔梗

用户：补气健脾用什么
输出：党参,黄芪,白术,甘草,山药

用户：味苦性寒清肝火的中药
输出：龙胆,黄连,黄芩,栀子,夏枯草

用户：{query}
输出："""
# 注意：如 query 与中医/药材完全无关（如编程、天气、股票），直接输出：无关


class LLMRewriter:
    def __init__(self, model: str = _DEFAULT_MODEL,
                 url: str = _DEFAULT_URL,
                 timeout: int = _DEFAULT_TIMEOUT,
                 cache_size: int = 512):
        self._model = model
        self._url = url.rstrip("/")
        self._timeout = timeout
        self._cache: "OrderedDict[str, List[str]]" = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.RLock()

    def enabled(self) -> bool:
        return os.environ.get(_ENV_ENABLED, "0") == "1"

    def needs_rewrite(self, query: str) -> bool:
        """启发式判断：短 query（<= 8 字）且不含症状词 → 不需要改写。"""
        q = (query or "").strip()
        if not q:
            return False
        if len(q) <= 8 and not any(kw in q for kw in _SYMPTOM_KW):
            return False
        return any(kw in q for kw in _SYMPTOM_KW) or len(q) > 8

    def _cache_get(self, query: str) -> Optional[List[str]]:
        with self._lock:
            v = self._cache.get(query)
            if v is not None:
                self._cache.move_to_end(query)
            return v

    def _cache_put(self, query: str, v: List[str]) -> None:
        with self._lock:
            self._cache[query] = v
            self._cache.move_to_end(query)
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

    def rewrite(self, query: str) -> List[str]:
        """返回药名列表（可为空）。失败静默返回 []。"""
        q = (query or "").strip()
        if not q:
            return []
        cached = self._cache_get(q)
        if cached is not None:
            return cached

        body = {
            "model": self._model,
            "prompt": _PROMPT.format(query=q),
            "stream": False,
            "keep_alive": "5m",
            "options": {"temperature": 0.1, "num_predict": 80},
        }
        try:
            req = urllib.request.Request(
                self._url + "/api/generate",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                d = json.load(r)
            text = (d.get("response") or "").strip()
            # [SANITY] LLM 幻觉过滤
            _low = text.lower()
            if any(k in text for k in ("无关", "没关系", "我是", "抱歉",
                                         "不清楚", "无法", "请提供")):
                self._cache_put(q, [])
                return []
            if len(text) > 100:
                self._cache_put(q, [])
                return []
            # 解析 CSV/中文逗号/换行
            parts = re.split(r"[，,\n]", text)
            names = []
            for p in parts:
                p = re.sub(r"^[0-9\.\-、\s]+", "", p).strip()
                # 只留 2-6 字中文（药名）
                if 1 < len(p) <= 8 and re.match(r"^[\u4e00-\u9fa5]+$", p):
                    names.append(p)
                if len(names) >= 8:
                    break
            self._cache_put(q, names)
            logger.info("[llm-rewrite] %r -> %s", q, names)
            return names
        except Exception as e:
            logger.debug("[llm-rewrite] 失败: %r", e)
            self._cache_put(q, [])
            return []


_DEFAULT: Optional[LLMRewriter] = None


def get_rewriter() -> LLMRewriter:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = LLMRewriter(
            model=os.environ.get(_ENV_MODEL, _DEFAULT_MODEL),
            url=os.environ.get(_ENV_URL, _DEFAULT_URL),
            timeout=int(os.environ.get(_ENV_TIMEOUT, _DEFAULT_TIMEOUT)))
    return _DEFAULT


__all__ = ["LLMRewriter", "get_rewriter"]
