"""Part 1 of loader.py."""
from __future__ import annotations
from backend.core.observability.silent import swallow

import os

import re

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any, Dict, List, Optional

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parents[4]

_ENV_FILE = _PROJECT_ROOT / ".env"

def _load_dotenv() -> None:
    """把 .env 读进 os.environ（不覆盖已有值）。"""
    if not _ENV_FILE.is_file():
        return
    try:
        with _ENV_FILE.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if not key:
                    continue
                # 不覆盖已有环境变量
                if key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        swallow("providers.config._loader_parts.part1:42", e)

_load_dotenv()

_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

_DEFAULT_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "llm_providers.yaml"
)

def _substitute_env(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    def repl(m: "re.Match[str]") -> str:
        return os.environ.get(m.group(1), "")
    return _ENV_RE.sub(repl, value)

@dataclass(frozen=True)
class ModelSpec:
    id: str
    display_name: str
    context_window: int
    max_output: int
    supports_tool_call: bool
    supports_stream: bool
    supports_embedding: bool
    cost_input_per_1k: float
    cost_output_per_1k: float
    strengths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "context_window": self.context_window,
            "max_output": self.max_output,
            "supports_tool_call": self.supports_tool_call,
            "supports_stream": self.supports_stream,
            "supports_embedding": self.supports_embedding,
            "cost_input_per_1k": self.cost_input_per_1k,
            "cost_output_per_1k": self.cost_output_per_1k,
            "strengths": list(self.strengths),
        }

@dataclass(frozen=True)
class ProviderSpec:
    name: str
    type: str
    display_name: str
    base_url: str
    api_key: str
    models: List[ModelSpec] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "display_name": self.display_name,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "models": [m.to_dict() for m in self.models],
        }

@dataclass(frozen=True)
class EmbeddingSpec:
    name: str
    provider: str
    model: str
    dimension: int = 0
    is_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider": self.provider,
            "model": self.model,
            "dimension": self.dimension,
            "default": self.is_default,
        }

@dataclass(frozen=True)
class RerankerSpec:
    name: str
    provider: str
    model: str
    is_default: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider": self.provider,
            "model": self.model,
            "default": self.is_default,
        }

@dataclass(frozen=True)
class VectorStoreSpec:
    driver: str = "chroma"
    path: str = "./vector_db"
    collection: str = "code_index"
    default_embedding: str = ""
    default_reranker: str = ""
    top_k: int = 10
    rerank_top_k: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "driver": self.driver,
            "path": self.path,
            "collection": self.collection,
            "default_embedding": self.default_embedding,
            "default_reranker": self.default_reranker,
            "top_k": self.top_k,
            "rerank_top_k": self.rerank_top_k,
        }

@dataclass(frozen=True)
class ModelRef:
    """一个已解析到具体 provider 的模型引用。"""
    provider: str
    model: str

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider, "model": self.model}

    def key(self) -> str:
        return f"{self.provider}/{self.model}"
