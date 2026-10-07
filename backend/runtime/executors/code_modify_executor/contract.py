"""Code modification executor 常量与内部数据类型。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

VERSION = "5.1"
NAME = "code_modify"

ProviderResult = Dict[str, Any]


@dataclass
class RequestData:
    """从 ExecutionNode 提取的请求数据。"""
    task: str
    files: List[str]
    source: Optional[str]
    instruction: str
    changes: Optional[Dict[str, Any]]
    path: Optional[str]
    workspace_root: str
