"""Agent Tools runtime 单例。职责：装配 registry / mounts / executor / history / gateway。
不挂路由（application_router 管）、不实现业务。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from dataclasses import dataclass
from typing import Any, Optional

from backend.agent_tools.executor import ToolExecutor
from backend.agent_tools.mounts import SessionMounts
from backend.agent_tools.registry import ToolRegistry, get_default_registry
from backend.agent_tools.session import SessionHistory, get_default_history

@dataclass(frozen=True)
class AgentToolsRuntime:
    registry: ToolRegistry
    mounts: SessionMounts
    executor: ToolExecutor
    history: SessionHistory
    gateway: Any = None

def _build_default_registry() -> tuple:
    """装配默认 registry + executor：注册 Domain + RAG 工具。"""
    from backend.agent_tools.contracts import ToolDomain
    from backend.agent_tools.executor import ToolExecutor
    from backend.agent_tools.providers import (
        DomainModule, make_domain_provider,
        RagToolSpec, make_rag_provider)
    from backend.agent_tools.registry import ToolRegistry

    reg = ToolRegistry()
    providers: list = []

    # Domain（必装，失败原因要打印，不静默）
    import sys as _sys
    for _name, _mod_path, _dom, _lm, _sm in [
        ("tcm", "backend.domain.providers.tcm", ToolDomain.TCM, "lookup", "search"),
        ("agriculture", "backend.domain.providers.agriculture",
         ToolDomain.AGRICULTURE, "lookup_term", "search_entities"),
        ("finance", "backend.domain.providers.finance",
         ToolDomain.FINANCE, "lookup_term", "search_entities"),
        ("law", "backend.domain.providers.law", ToolDomain.GENERAL, "lookup", "search"),
        ("medicine", "backend.domain.providers.medicine", ToolDomain.GENERAL, "lookup", "search"),
        ("history", "backend.domain.providers.history", ToolDomain.GENERAL, "lookup", "search"),
    ]:
        try:
            _m = __import__(_mod_path, fromlist=[_lm, _sm])
            _display = {"tcm": "中医", "agriculture": "农业",
                        "finance": "金融", "law": "法律",
                        "medicine": "医疗", "history": "历史"}[_name]
            _p = make_domain_provider([
                DomainModule(_name, _display, _dom, _m,
                             lookup_method=_lm, search_method=_sm)])
            reg.register_many(_p.descriptors())
            providers.append(_p)
        except Exception as _e:
            print(f"[agent_tools] domain {_name} 装配失败: "
                  f"{type(_e).__name__}: {_e}", file=_sys.stderr)

    # 图片向量检索（可选：CLIP/图片库不可用则跳过）
    try:
        from backend.agent_tools.providers.image_provider import (
            make_image_provider)
        from backend.rag.image_index import (
            get_default_image_store, make_clip_engine,
            make_image_retriever)
        img_store = get_default_image_store()
        clip = make_clip_engine()
        img_r = make_image_retriever(engine=clip, store=img_store)
        ip = make_image_provider(retriever=img_r)
        reg.register_many(ip.descriptors())
        providers.append(ip)
    except Exception as _e:
        import sys as _sys
        print(f"[agent_tools] image provider 装配失败: "
              f"{type(_e).__name__}: {_e}", file=_sys.stderr)

    # RAG（可选：VectorStore 不可用则跳过）
    try:
        from backend.api.rag.multimodal_runtime import get_multimodal_rag_runtime
        svc = get_multimodal_rag_runtime().service
        specs = [
            RagToolSpec(
                "rag.search_tcm",
                "中医知识库检索（症状/病因/药材/方剂/性味归经）",
                ToolDomain.TCM, where={"kb": "tcm"}),
            RagToolSpec(
                "rag.search_agriculture",
                "农业知识库检索（作物/育种/病虫害/农药/土壤）",
                ToolDomain.AGRICULTURE, where={"kb": "agriculture"}),
            RagToolSpec(
                "rag.search_finance",
                "金融知识库检索（证券/基金/保险/银行/投资）",
                ToolDomain.FINANCE, where={"kb": "finance"}),
            RagToolSpec(
                "rag.search_kb",
                "通用知识库检索（跨领域，未分类内容）",
                ToolDomain.GENERAL, where={"kb": "general"}),
        ]
        p = make_rag_provider(svc, specs)
        reg.register_many(p.descriptors())
        providers.append(p)
    except Exception as e:
        swallow("agent_tools.runtime:104", e)

    return reg, ToolExecutor(providers=providers)

def _build_default_gateway() -> Any:
    """尝试用 OllamaClient 构造 gateway；失败时降级 EchoGateway。"""
    try:
        from backend.agent_tools.gateway import make_gateway
        from backend.providers.runtime.ollama_client import OllamaClient
        return make_gateway(OllamaClient(), default_model="qwen3:8b")
    except Exception:
        from backend.agent_tools.gateway import EchoGateway
        return EchoGateway()

def build_agent_tools_runtime(*, registry: Optional[ToolRegistry] = None,
                              executor: Optional[ToolExecutor] = None,
                              gateway: Any = None) -> AgentToolsRuntime:
    if registry is None and executor is None:
        reg, ex = _build_default_registry()
    else:
        reg = registry or get_default_registry()
        ex = executor or ToolExecutor(providers=())
    gw = gateway if gateway is not None else _build_default_gateway()
    return AgentToolsRuntime(
        registry=reg, mounts=SessionMounts(),
        executor=ex, history=get_default_history(), gateway=gw)

_RT: Optional[AgentToolsRuntime] = None

def get_agent_tools_runtime() -> AgentToolsRuntime:
    global _RT
    if _RT is None:
        _RT = build_agent_tools_runtime()
    return _RT

def set_agent_tools_runtime(rt: Optional[AgentToolsRuntime]) -> None:
    global _RT
    _RT = rt

__all__ = ["AgentToolsRuntime", "build_agent_tools_runtime",
           "get_agent_tools_runtime", "set_agent_tools_runtime"]
