"""完整 RAG QA 链路（工业级）。

流程：
  query → 双路检索（文本 + 图片）→ 重排 → 组装 prompt → LLM 生成 → {answer, citations, images}

职责：只编排。不编码、不存储、不做前端。
配置（env）：
  RAG_QA_ENABLED=1
  RAG_QA_MODEL      LLM 模型（默认 gemma3:latest —— 非推理模型，输出稳定）
  RAG_QA_OLLAMA_URL Ollama 地址
  RAG_QA_TIMEOUT    超时秒（默认 120）

关于推理模型（qwen3.5 等）：它们输出分 thinking + response 两段，
本模块会优先取 response，若空则从 thinking 里剥最终答案。
"""
from __future__ import annotations
import json
import logging
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_ENV_ENABLED = "RAG_QA_ENABLED"
_ENV_MODEL = "RAG_QA_MODEL"
_ENV_URL = "RAG_QA_OLLAMA_URL"
_ENV_TIMEOUT = "RAG_QA_TIMEOUT"
from backend.rag.plugins import model_resolver as _resolver

_DEFAULT_MODEL = _resolver.default_chat_model() or ""

_DEFAULT_URL = "http://127.0.0.1:11434"
_DEFAULT_TIMEOUT = 120

_SYSTEM_PROMPT = (
    "你是中医知识助手。请严格遵守以下规则：\n"
    "1. 只根据【参考资料】回答问题。\n"
    "2. 如果参考资料不足以回答，直接说\"根据现有资料无法回答\"。\n"
    "3. 回答要简洁专业，引用原文时标注 [1][2] 等编号。\n"
    "4. 不要编造资料中没有的内容。\n"
)

_TWO_NEWLINE = chr(10) + chr(10)


def enabled() -> bool:
    return os.environ.get(_ENV_ENABLED, "0") == "1"


def _model() -> str:
    return os.environ.get(_ENV_MODEL, _DEFAULT_MODEL)


def _url() -> str:
    return os.environ.get(_ENV_URL, _DEFAULT_URL).rstrip("/")


def _timeout() -> int:
    try:
        return int(os.environ.get(_ENV_TIMEOUT, _DEFAULT_TIMEOUT))
    except Exception:
        return _DEFAULT_TIMEOUT


@dataclass
class QAResult:
    query: str = ""
    answer: str = ""
    citations: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "citations": self.citations,
            "images": self.images,
            "meta": self.meta,
        }


def _pick_response(data: dict) -> str:
    """从 Ollama 返回里提取最终答案（兼容 thinking 模型）。"""
    resp = (data.get("response") or "").strip()
    if resp:
        return resp
    thinking = (data.get("thinking") or "").strip()
    if not thinking:
        return ""
    for pat in [r"Final Answer[：:\s]+(.+)",
                r"最终答案[：:\s]+(.+)",
                r"答案[：:\s]+(.+)"]:
        m = re.search(pat, thinking, re.DOTALL)
        if m:
            return m.group(1).strip()[:600]
    tail = thinking.split(_TWO_NEWLINE)[-1].strip()
    return tail[:600] if len(tail) > 20 else ""


def _build_evidence(query: str, k_text: int = 3,
                    k_img: int = 8) -> Dict[str, Any]:
    from backend.rag.retrieval_orchestrator import get_orchestrator
    orch = get_orchestrator()
    result = orch.search(query, k_text=k_text, k_img=k_img)
    return result.to_dict()


def _build_prompt(query: str, citations: List[Dict[str, Any]],
                   history: Optional[List[str]] = None) -> str:
    if not citations:
        evidence = "（无参考资料）"
    else:
        parts = []
        for i, c in enumerate(citations, 1):
            title = c.get("doc_title") or "(未知)"
            page = c.get("page")
            page_s = f"第{page}页" if page else ""
            text = (c.get("text") or "").strip()[:800]
            parts.append(f"[{i}] 《{title}》{page_s}" + chr(10) + text)
        evidence = (chr(10) + chr(10)).join(parts)
    ctx = ""
    if history:
        recent = [h for h in history[-4:] if h and h.strip()]
        if recent:
            ctx = ("【对话历史】" + chr(10) +
                   (chr(10).join(f"- {h[:200]}" for h in recent)) +
                   chr(10) + chr(10))
    return (
        ctx +
        "【参考资料】" + chr(10) + evidence + chr(10) + chr(10) +
        "【问题】" + chr(10) + query + chr(10) + chr(10) +
        "请根据参考资料回答："
    )


def _call_llm(prompt: str) -> str:
    body = {
        "model": _model(),
        "prompt": prompt,
        "system": _SYSTEM_PROMPT,
        "stream": False,
        "keep_alive": "5m",
        "options": {
            "temperature": 0.2,
            "num_predict": 1024,
        },
    }
    req = urllib.request.Request(
        _url() + "/api/generate",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_timeout()) as r:
            d = json.load(r)
        text = _pick_response(d)
        if not text:
            logger.warning(
                "[rag-qa] LLM 空返回 model=%s done_reason=%s "
                "thinking=%d字 response=%d字",
                _model(), d.get("done_reason"),
                len(d.get("thinking") or ""), len(d.get("response") or ""))
        return text
    except Exception as e:
        logger.warning("[rag-qa] LLM 失败: %r", e)
        return ""


def answer(query: str, *, k_text: int = 3, k_img: int = 8,
           generate: bool = True,
           history: Optional[List[str]] = None) -> QAResult:
    """完整 RAG QA。

    Args:
        history: 可选。历史用户/助手消息（旧→新），用于：
          1. 指代消解（"它/此方" → 上轮实体）
          2. Prompt 上下文（multi-turn 提升连贯性）
    """
    q = (query or "").strip()

    # [MULTI_TURN] 指代消解：用 query_rewriter 把"它/此方"替换为上轮实体
    if history and q:
        try:
            from backend.agent_tools.query_rewriter import rewrite as _rw
            q = _rw(q, history) or q
        except Exception:
            pass
    if not q:
        return QAResult(query=q, meta={"error": "empty_query"})

    ev = _build_evidence(q, k_text=k_text, k_img=k_img)
    citations = ev.get("text_hits") or []
    images = ev.get("images") or []

    answer_text = ""
    if generate and citations:
        prompt = _build_prompt(q, citations, history)
        answer_text = _call_llm(prompt)
    elif generate and not citations:
        answer_text = "根据现有资料无法回答。"

    return QAResult(
        query=q,
        answer=answer_text or "根据现有资料无法回答。",
        citations=citations,
        images=images,
        meta={
            "n_citations": len(citations),
            "n_images": len(images),
            "models": {
                "retriever": "qwen3-emb + BGE",
                "reranker": "Qwen3-Reranker",
                "generator": _model(),
            },
        },
    )


__all__ = ["QAResult", "answer", "enabled"]
