"""领域 provider → Agent 工具 provider。
职责：把 domain provider 模块（tcm/agriculture/finance 等）暴露为
`domain.lookup.<id>` 与 `domain.search.<id>` 两类工具。
不做注册（registry 管）、不调 MCP（client 管）、不组装最终响应。
与 backend/domain/providers/* 边界：domain 模块管词表与 lookup；
本 provider 管"暴露成哪些工具名 + 参数解析"。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Sequence

from backend.agent_tools.contracts import (
    ToolCall, ToolCategory, ToolDescriptor, ToolDomain, ToolResult)

@dataclass(frozen=True)
class DomainModule:
    """一个领域模块的适配描述。
    lookup_method / search_method 允许不同 provider 用不同方法名。"""
    id: str
    display: str
    domain: ToolDomain
    module: Any
    lookup_method: str = "lookup"
    search_method: str = "search"

    def __post_init__(self) -> None:
        import types
        if not self.id.strip(): raise ValueError("DomainModule.id required")
        if not self.display.strip(): raise ValueError("DomainModule.display required")
        if self.module is None: raise ValueError("DomainModule.module required")
        # 若是类 → 自动实例化
        target = self.module
        if isinstance(target, type):
            try:
                target = target()
            except Exception as e:
                raise TypeError(f"{self.id} 类实例化失败: {e}") from e
            object.__setattr__(self, "module", target)
        # 若是模块但缺 lookup/search，尝试从模块里找同名类
        if not callable(getattr(target, self.lookup_method, None)):
            for name in dir(target):
                obj = getattr(target, name)
                if isinstance(obj, type) and callable(
                        getattr(obj, self.lookup_method, None)):
                    inst = obj()
                    object.__setattr__(self, "module", inst)
                    target = inst
                    break
        lookup_m = self.lookup_method
        search_m = self.search_method
        if not callable(getattr(target, lookup_m, None)):
            raise TypeError(
                f"{self.id} 缺 {lookup_m}()（可传 lookup_method= 改名）")
        if not callable(getattr(target, search_m, None)):
            raise TypeError(
                f"{self.id} 缺 {search_m}()（可传 search_method= 改名）")

class DomainToolProvider:
    def __init__(self, modules: Sequence[DomainModule]) -> None:
        if not modules:
            raise ValueError("modules required")
        self._mods = tuple(modules)
        self._by_id = {m.id: m for m in self._mods}
        if len(self._by_id) != len(self._mods):
            raise ValueError("DomainModule.id must be unique")

    # ---------- 工具生成 ----------
    def descriptors(self) -> list[ToolDescriptor]:
        out: list[ToolDescriptor] = []
        for m in self._mods:
            out.append(ToolDescriptor(
                name=f"domain.lookup.{m.id}",
                description=f"{m.display} 术语释义查询",
                category=ToolCategory.DOMAIN, domain=m.domain,
                server="local", tags=("domain", m.id),
                meta={"op": "lookup", "domain_id": m.id},
            ))
            out.append(ToolDescriptor(
                name=f"domain.search.{m.id}",
                description=f"{m.display} 关键词检索",
                category=ToolCategory.DOMAIN, domain=m.domain,
                server="local", tags=("domain", m.id),
                meta={"op": "search", "domain_id": m.id},
            ))
        return out

    def can_handle(self, name: str) -> bool:
        parts = name.split(".")
        return (len(parts) == 3 and parts[0] == "domain"
                and parts[1] in ("lookup", "search")
                and parts[2] in self._by_id)

    # ---------- 执行 ----------
    def execute(self, call: ToolCall) -> ToolResult:
        parts = call.name.split(".")
        if len(parts) != 3 or parts[0] != "domain":
            return ToolResult(name=call.name, ok=False,
                              error=f"bad domain tool name: {call.name}")
        op, domain_id = parts[1], parts[2]
        mod = self._by_id.get(domain_id)
        if mod is None:
            return ToolResult(name=call.name, ok=False,
                              error=f"unknown domain: {domain_id}")
        if op == "lookup":
            return self._lookup(call.name, mod, call.arguments)
        if op == "search":
            return self._search(call.name, mod, call.arguments)
        return ToolResult(name=call.name, ok=False,
                          error=f"unknown op: {op}")

    @staticmethod
    def _lookup(name: str, mod: DomainModule,
                args) -> ToolResult:
        term = str(args.get("term", "")).strip()
        if not term:
            return ToolResult(name=name, ok=False, error="term required")
        # [MULTI_TURN] 从 args 里拿 history（agent_loop 已注入）
        history = args.get("_history") or args.get("history") or None
        if isinstance(history, str):
            history = [history]
        try:
            # 尝试带 history 调用；不支持则回退
            try:
                val = getattr(mod.module, mod.lookup_method)(
                    term, history=history)
            except TypeError:
                val = getattr(mod.module, mod.lookup_method)(term)
        except Exception as e:
            return ToolResult(name=name, ok=False,
                              error=f"{type(e).__name__}: {e}")
        if val is None:
            return ToolResult(name=name, ok=True, output="(未收录)",
                              meta={"found": False, "term": term})
        # [IMG_BRIDGE] dict 返回 → 提取 answer + images + citations
        if isinstance(val, dict):
            answer = str(val.get("answer", "") or "")
            images = val.get("images") or []
            citations = val.get("citations") or []
            return ToolResult(
                name=name, ok=True, output=answer,
                meta={"found": True, "term": term,
                      "images": images,
                      "citations": citations,
                      "source": val.get("source", "")})
        return ToolResult(name=name, ok=True, output=str(val),
                          meta={"found": True, "term": term})

    @staticmethod
    def _search(name: str, mod: DomainModule,
                args) -> ToolResult:
        # 兼容 keyword / term / query 三个键名（LLM 输出不稳定）
        kw = str(args.get("keyword") or args.get("term")
                 or args.get("query") or "").strip()
        if not kw:
            return ToolResult(name=name, ok=False, error="keyword required")
        try:
            hits = getattr(mod.module, mod.search_method)(kw)
        except Exception as e:
            return ToolResult(name=name, ok=False,
                              error=f"{type(e).__name__}: {e}")
        lst = list(hits or [])
        out = "\n".join(f"- {x}" for x in lst) if lst else "(无匹配)"
        return ToolResult(name=name, ok=True, output=out,
                          meta={"count": len(lst), "keyword": kw})

def make_domain_provider(modules: Sequence[DomainModule]) -> DomainToolProvider:
    return DomainToolProvider(modules)

__all__ = ["DomainModule", "DomainToolProvider", "make_domain_provider"]
