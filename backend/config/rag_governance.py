"""RAG 治理配置（数据 + 阈值统一入口）。

设计：
    - 数据：backend/data/*.json（关键词 / URL / 标签 / 停用词）
    - 阈值：环境变量（RAG_* 前缀）
    - 无 pydantic 依赖（对齐 backend/config/constants/endpoints.py 模式）
    - 单例 + 惰性缓存（模块级）

用法：
    from backend.config.rag_governance import rag_cfg
    rag_cfg.intent_keywords   # frozenset[str]
    rag_cfg.max_images        # int
    rag_cfg.domain_images     # dict
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, FrozenSet, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"

# ── env 读取辅助（带类型转换 + 默认值）──


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _load_json(name: str) -> Dict[str, Any]:
    """读 backend/data/<name>；失败返回 {}（不阻塞启动）。"""
    p = DATA_DIR / name
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


class RagGovernanceSettings:
    """RAG 治理配置。

    职责：
        - 读 backend/data/*.json（数据外置）
        - 读 RAG_* 环境变量（阈值覆盖）
        - 提供统一访问接口

    不负责：
        - 业务逻辑
        - 与具体 RAG 实现耦合
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        # ── 阈值（env 覆盖）──
        self.max_auto_prompt_len: int = _env_int("RAG_MAX_AUTO_PROMPT_LEN", 30)
        self.max_images: int = _env_int("RAG_MAX_IMAGES", 2)
        self.min_image_score: float = _env_float("RAG_MIN_IMAGE_SCORE", 0.3)
        self.min_faith: float = _env_float("RAG_MIN_FAITH", 0.6)
        self.min_relevance: float = _env_float("RAG_MIN_RELEVANCE", 0.5)
        # evaluator 分级阈值
        self.faith_fail: float = _env_float("RAG_FAITH_FAIL", 0.60)
        self.faith_pass: float = _env_float("RAG_FAITH_PASS", 0.85)
        self.relevance_min: float = _env_float("RAG_RELEVANCE_MIN", 0.50)
        self.coverage_min: float = _env_float("RAG_COVERAGE_MIN", 0.40)
        self.default_budget_ms: int = _env_int("RAG_DEFAULT_BUDGET_MS", 3000)
        self.default_top_k: int = _env_int("RAG_DEFAULT_TOP_K", 3)
        self.max_context_chars: int = _env_int("RAG_MAX_CONTEXT_CHARS", 2000)

        # ── 数据缓存（惰性加载）──
        self._intent_kw: FrozenSet[str] | None = None
        self._domain_kw: Dict[str, List[str]] | None = None
        self._domain_tools: Dict[str, List[str]] | None = None
        self._field_labels: Dict[str, str] | None = None
        self._domain_images: Dict[str, Dict[str, List[Dict[str, str]]]] | None = None
        self._stopwords: FrozenSet[str] | None = None

    # ── 数据访问（惰性）──

    @property
    def intent_keywords(self) -> FrozenSet[str]:
        if self._intent_kw is None:
            data = _load_json("rag_intent_keywords.json")
            self._intent_kw = frozenset(data.get("keywords", []))
        return self._intent_kw

    @property
    def domain_keywords(self) -> Dict[str, List[str]]:
        """返回 {domain: [keywords]}。

        兼容两种数据格式：
            旧：{"domains": {"tcm": ["中医", ...]}}
            新：{"domains": {"tcm": {"keywords": [...], "tools": [...]}}}
        """
        if self._domain_kw is None:
            data = _load_json("rag_domain_keywords.json")
            raw = data.get("domains", {})
            out: Dict[str, List[str]] = {}
            for name, val in raw.items():
                if isinstance(val, dict):
                    out[name] = list(val.get("keywords", []))
                elif isinstance(val, (list, tuple)):
                    out[name] = list(val)
            self._domain_kw = out
        return self._domain_kw

    @property
    def domain_tools(self) -> Dict[str, List[str]]:
        """返回 {domain: [tool_names]}。"""
        if self._domain_tools is None:
            data = _load_json("rag_domain_keywords.json")
            raw = data.get("domains", {})
            out: Dict[str, List[str]] = {}
            for name, val in raw.items():
                if isinstance(val, dict):
                    out[name] = list(val.get("tools", []))
            out[self.general_domain] = list(data.get("general_tools", ["chat"]))
            self._domain_tools = out
        return self._domain_tools

    @property
    def general_domain(self) -> str:
        """回退领域名（默认 "general"）。"""
        data = _load_json("rag_domain_keywords.json")
        return str(data.get("general_domain", "general"))

    @property
    def field_labels(self) -> Dict[str, str]:
        if self._field_labels is None:
            data = _load_json("rag_field_labels.json")
            self._field_labels = dict(data.get("labels", {}))
        return self._field_labels

    @property
    def domain_images(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        if self._domain_images is None:
            data = _load_json("rag_domain_images.json")
            self._domain_images = {
                domain: {name: list(imgs) for name, imgs in items.items()}
                for domain, items in data.get("images", {}).items()
            }
        return self._domain_images

    @property
    def stopwords(self) -> FrozenSet[str]:
        if self._stopwords is None:
            data = _load_json("rag_stopwords_zh.json")
            self._stopwords = frozenset(data.get("stopwords", []))
        return self._stopwords

    def dump(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "thresholds": {
                "max_auto_prompt_len": self.max_auto_prompt_len,
                "max_images": self.max_images,
                "min_image_score": self.min_image_score,
                "min_faith": self.min_faith,
                "min_relevance": self.min_relevance,
                "faith_fail": self.faith_fail,
                "faith_pass": self.faith_pass,
                "relevance_min": self.relevance_min,
                "coverage_min": self.coverage_min,
                "default_budget_ms": self.default_budget_ms,
                "default_top_k": self.default_top_k,
                "max_context_chars": self.max_context_chars,
            },
            "data_sizes": {
                "intent_keywords": len(self.intent_keywords),
                "domain_keywords": len(self.domain_keywords),
                "domain_tools": len(self.domain_tools),
                "field_labels": len(self.field_labels),
                "domain_images": sum(len(v) for v in self.domain_images.values()),
                "stopwords": len(self.stopwords),
            },
        }


@lru_cache(maxsize=1)
def get_rag_config() -> RagGovernanceSettings:
    """单例（测试可 clear）。"""
    return RagGovernanceSettings()


rag_cfg = get_rag_config()

__all__ = ["RagGovernanceSettings", "get_rag_config", "rag_cfg", "DATA_DIR"]
