"""Build + register domain tools into the frozen ToolRuntime."""
from __future__ import annotations

from typing import List

from backend.agent.tools.domain.domain_lookup import DomainLookupTool
from backend.agent.tools.domain.domain_search import DomainSearchTool
from backend.agent.tools.domain.domain_term import DomainTermTool
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.domain.registry import DomainRegistry
from backend.runtime.tools.runtime import ToolRuntime


def build_domain_tools(
    domain_registry: DomainRegistry,
) -> List[RuntimeToolProtocol]:
    return [
        DomainLookupTool(domain_registry),
        DomainTermTool(domain_registry),
        DomainSearchTool(domain_registry),
    ]


def register_domain_tools(
    tool_runtime: ToolRuntime,
    domain_registry: DomainRegistry,
) -> None:
    for tool in build_domain_tools(domain_registry):
        tool_runtime.register_tool(tool)


def build_default_domain_registry() -> DomainRegistry:
    from backend.domain.providers import (
        AgricultureProvider, FinanceProvider,
    )
    reg = DomainRegistry()
    reg.register_all([AgricultureProvider(), FinanceProvider()])
    return reg
