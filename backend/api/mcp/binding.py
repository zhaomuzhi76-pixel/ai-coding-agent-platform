"""McpBinding: HTTP adapter over MCP / local tool registry."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.agent.tools.domain import build_domain_tools
from backend.agent.tools.domain.registry_extension import (
    build_default_domain_registry,
)
from backend.rag.service import get_rag_service
from backend.rag.tools.rag_tools import build_rag_tools


class McpBinding:
    VERSION = "1.0"
    PREFIX = "/api/mcp"

    def __init__(self) -> None:
        self._domain_registry = build_default_domain_registry()

    def tools(self) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []

        # ── domain 工具（本地注册）──
        for t in build_domain_tools(self._domain_registry):
            schema = t.schema()
            out.append({
                "name": schema.name,
                "description": schema.description,
                "category": "domain",
                "exposed": True,
                "param_count": len(schema.parameters),
            })

        # ── RAG 工具（自己封装 · 后端能力）──
        try:
            for t in build_rag_tools(get_rag_service()):
                schema = t.schema()
                out.append({
                    "name": schema.name,
                    "description": schema.description,
                    "category": "rag",
                    "exposed": True,
                    "param_count": len(schema.parameters),
                })
        except Exception as exc:
            print(f"[mcp] rag tools failed: {exc}", flush=True)

        return {"tools": out, "count": len(out)}

    def servers(self) -> Dict[str, Any]:
        # 远端 MCP server 注册表尚未接入（需要持久层或 runtime 状态）
        return {"servers": [], "count": 0,
                "note": "远端 server 注册表待接入"}

    def domains(self) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []
        for name in self._domain_registry.names():
            p = self._domain_registry.resolve(name)
            out.append({
                "name": name,
                "entity_types": p.list_entity_types(),
                "terms": len(p.list_terms()),
            })
        return {"domains": out, "count": len(out)}

    def summary(self) -> Dict[str, Any]:
        t = self.tools()
        s = self.servers()
        d = self.domains()
        return {
            "local_tools": t["count"],
            "remote_servers": s["count"],
            "domains": d["count"],
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }


__all__ = ["McpBinding"]
