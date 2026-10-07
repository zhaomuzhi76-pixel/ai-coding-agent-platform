"""L1 · Task Router（单一职责：按任务类型路由到 Agent）。

策略：
  · 关键词 → 能力（每条规则独立，避免连续子串陷阱）
  · 能力 → 候选 Agent（Registry 按 priority 排序）
  · 首个命中 → RouteDecision

不做：执行、消息、状态。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from backend.application.multi_agent.agent_registry import (
    AgentDescriptor, AgentRegistry, get_default_registry,
)


# ★ 修正：每条规则一个关键词，避免"设计一个方案"匹配"设计方案"的问题
_INTENT_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    # 规划类（拆成多个关键词）
    ("规划",     ("planning", "task_decomposition")),
    ("设计",     ("planning", "task_decomposition")),
    ("方案",     ("planning", "task_decomposition")),
    ("拆解",     ("planning", "task_decomposition")),
    ("计划",     ("planning", "task_decomposition")),
    ("plan",     ("planning", "task_decomposition")),
    # 审核类
    ("审核",     ("code_review", "quality_check")),
    ("审查",     ("code_review", "quality_check")),
    ("检查",     ("code_review", "quality_check")),
    ("review",   ("code_review", "quality_check")),
    # 编码类
    ("写代码",   ("code_generate",)),
    ("生成代码", ("code_generate",)),
    ("修复",     ("code_modify",)),
    ("修改",     ("code_modify",)),
    ("重构",     ("code_edit",)),
    ("创建文件", ("file_write",)),
    ("读取文件", ("file_read",)),
    # RAG 类
    ("是什么",   ("knowledge_qa",)),
    ("功效",     ("knowledge_qa",)),
    ("主治",     ("knowledge_qa",)),
    ("图片",     ("image_search",)),
    ("长什么样", ("image_search",)),
    ("介绍",     ("knowledge_qa",)),
    # 通用
    ("你好",     ("chat", "general_qa")),
)


@dataclass(frozen=True)
class RouteDecision:
    task: str
    intent: str
    candidates: Tuple[AgentDescriptor, ...] = ()
    chosen: Optional[AgentDescriptor] = None
    reason: str = ""
    fallback: bool = False

    @property
    def agent_id(self) -> str:
        return self.chosen.agent_id if self.chosen else ""


class TaskRouter:
    """任务路由器（无状态）。"""

    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        self._reg = registry or get_default_registry()

    def _match_caps(self, text: str) -> Tuple[str, ...]:
        if not text:
            return ()
        caps: List[str] = []
        for kw, cap_set in _INTENT_RULES:
            if kw in text:
                for c in cap_set:
                    if c not in caps:
                        caps.append(c)
        return tuple(caps)

    def _try_llm_fallback(self, task: str) -> "Optional[RouteDecision]":
        """LLM 兜底（env RAG_MA_LLM_INTENT=1）。失败返 None。"""
        try:
            from backend.application.multi_agent import task_router_llm as _llm
            if not _llm.is_enabled():
                return None
            r = _llm.classify(task)
            if not r:
                return None
            aid = r.get("agent", "")
            desc = self._reg.get(aid)
            if desc is None:
                return None
            return RouteDecision(
                task=task,
                intent="llm:{}".format(aid),
                candidates=(desc,),
                chosen=desc,
                reason="llm classify: {} (conf={})".format(
                    aid, r.get("confidence", "?")),
                fallback=False,
            )
        except Exception:
            return None

    def route(self, task: str) -> RouteDecision:
        text = (task or "").strip()
        if not text:
            return RouteDecision(task=text, intent="empty", fallback=True)

        caps = self._match_caps(text)
        candidates: List[AgentDescriptor] = []
        for cap in caps:
            for a in self._reg.find_by_capability(cap):
                if a not in candidates:
                    candidates.append(a)

        if candidates:
            return RouteDecision(
                task=text, intent=",".join(caps),
                candidates=tuple(candidates),
                chosen=candidates[0],
                reason="keyword match: {}".format(caps[0]),
            )

        # [LLM] 关键词未命中 → LLM 兜底（env 开关 · 默认关闭）
        llm_d = self._try_llm_fallback(text)
        if llm_d is not None:
            return llm_d

        chat_agents = self._reg.find_by_role("chat")
        if chat_agents:
            return RouteDecision(
                task=text, intent="fallback",
                candidates=tuple(chat_agents),
                chosen=chat_agents[0],
                reason="no keyword matched, fallback to chat",
                fallback=True,
            )
        return RouteDecision(task=text, intent="none", fallback=True)

    def route_topn(self, task: str, n: int = 3) -> Tuple[AgentDescriptor, ...]:
        d = self.route(task)
        return d.candidates[:max(1, n)]

    def dump(self) -> Dict[str, Any]:
        return {"rules": len(_INTENT_RULES),
                "registry_size": self._reg.count()}


_DEFAULT: Optional[TaskRouter] = None


def get_default_router() -> TaskRouter:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = TaskRouter()
    return _DEFAULT


__all__ = ["TaskRouter", "RouteDecision", "get_default_router"]
