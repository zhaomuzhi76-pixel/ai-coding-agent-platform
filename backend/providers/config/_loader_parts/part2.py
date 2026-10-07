"""Part 2 of loader.py."""
from __future__ import annotations
from .part1 import (Any, Dict, List, Optional, dataclass, field,)  # noqa
from .part1 import EmbeddingSpec  # noqa
from .part1 import ModelRef  # noqa
from .part1 import ModelSpec  # noqa
from .part1 import ProviderSpec  # noqa
from .part1 import RerankerSpec  # noqa
from .part1 import VectorStoreSpec  # noqa
from .part1 import _substitute_env  # noqa

@dataclass
class LLMConfig:
    providers: List[ProviderSpec] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    source: str = ""
    default_provider: str = ""
    default_model: str = ""
    agent_routing: Dict[str, List[ModelRef]] = field(default_factory=dict)
    embeddings: List[EmbeddingSpec] = field(default_factory=list)
    rerankers: List[RerankerSpec] = field(default_factory=list)
    vector_store: VectorStoreSpec = field(default_factory=VectorStoreSpec)

    def all_models(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for p in self.providers:
            for m in p.models:
                out.append({
                    "model": m.id,
                    "provider": p.name,
                    "provider_type": p.type,
                    "display_name": m.display_name,
                    "context_window": m.context_window,
                    "max_output": m.max_output,
                    "supports_tool_call": m.supports_tool_call,
                    "supports_stream": m.supports_stream,
                    "supports_embedding": m.supports_embedding,
                    "cost_input_per_1k": m.cost_input_per_1k,
                    "cost_output_per_1k": m.cost_output_per_1k,
                    "strengths": list(m.strengths),
                })
        return out

    def routing_chain(self, role: str) -> List[ModelRef]:
        """取某角色的模型链；无配置则退回 default。"""
        chain = self.agent_routing.get(role)
        if chain:
            return list(chain)
        if self.default_provider and self.default_model:
            return [ModelRef(
                provider=self.default_provider,
                model=self.default_model,
            )]
        return []

    def default_embedding(self) -> Optional[EmbeddingSpec]:
        for e in self.embeddings:
            if e.is_default:
                return e
        return self.embeddings[0] if self.embeddings else None

    def default_reranker(self) -> Optional[RerankerSpec]:
        for r in self.rerankers:
            if r.is_default:
                return r
        return self.rerankers[0] if self.rerankers else None

    def embedding_by_name(
        self, name: str,
    ) -> Optional[EmbeddingSpec]:
        for e in self.embeddings:
            if e.name == name:
                return e
        return None

    def dump(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "providers": [p.to_dict() for p in self.providers],
            "skipped": list(self.skipped),
            "model_count": sum(len(p.models) for p in self.providers),
            "default_provider": self.default_provider,
            "default_model": self.default_model,
            "agent_routing": {
                role: [r.to_dict() for r in chain]
                for role, chain in self.agent_routing.items()
            },
            "embeddings": [e.to_dict() for e in self.embeddings],
            "rerankers": [r.to_dict() for r in self.rerankers],
            "vector_store": self.vector_store.to_dict(),
        }

_REQUIRE_KEY = {"dashscope", "anthropic", "openai_compatible"}

def _parse_model(raw: Dict[str, Any]) -> ModelSpec:
    mid = str(raw.get("id", "")).strip()
    if not mid:
        raise ValueError("model.id required")
    return ModelSpec(
        id=mid,
        display_name=str(raw.get("display_name", mid)),
        context_window=int(raw.get("context_window", 32768)),
        max_output=int(raw.get("max_output", 8192)),
        supports_tool_call=bool(raw.get("supports_tool_call", False)),
        supports_stream=bool(raw.get("supports_stream", True)),
        supports_embedding=bool(raw.get("supports_embedding", False)),
        cost_input_per_1k=float(raw.get("cost_input_per_1k", 0.0)),
        cost_output_per_1k=float(raw.get("cost_output_per_1k", 0.0)),
        strengths=list(raw.get("strengths", []) or []),
    )

def _parse_provider(raw: Dict[str, Any]) -> Optional[ProviderSpec]:
    name = str(raw.get("name", "")).strip()
    ptype = str(raw.get("type", "")).strip()
    if not name or not ptype:
        return None
    base_url = str(_substitute_env(raw.get("base_url", ""))).strip()
    api_key = str(_substitute_env(raw.get("api_key", ""))).strip()

    if ptype in _REQUIRE_KEY and not api_key:
        return None
    if ptype == "openai_compatible" and not base_url:
        return None

    models_raw = raw.get("models", []) or []
    models = [_parse_model(m) for m in models_raw if isinstance(m, dict)]
    # ollama 类型允许 models 为空（模型由 discovery 动态发现）
    # 但为了让 provider 能被注册进 registry，需要至少 1 个 ModelSpec
    # 用哨兵占位，API 层会过滤掉（__ 前缀）
    if not models and ptype == "ollama":
        models = [_parse_model({
            "id": "__discovery_placeholder__",
            "display_name": "(自动发现)",
            "context_window": 0,
            "max_output": 0,
            "supports_tool_call": False,
            "supports_stream": False,
            "supports_embedding": False,
            "cost_input_per_1k": 0.0,
            "cost_output_per_1k": 0.0,
            "strengths": [],
        })]
    if not models:
        return None

    return ProviderSpec(
        name=name, type=ptype,
        display_name=str(raw.get("display_name", name)),
        base_url=base_url, api_key=api_key, models=models,
    )

def _parse_model_ref(raw: Any) -> Optional[ModelRef]:
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if "/" not in s:
        return None
    prov, _, model = s.partition("/")
    prov, model = prov.strip(), model.strip()
    if not prov or not model:
        return None
    return ModelRef(provider=prov, model=model)

def _parse_routing(
    raw: Any, providers: List[ProviderSpec],
) -> Dict[str, List[ModelRef]]:
    """过滤掉未注册 provider / 未定义 model 的引用。"""
    if not isinstance(raw, dict):
        return {}
    # 索引：provider_name → set(model_ids)
    index: Dict[str, set] = {
        p.name: {m.id for m in p.models} for p in providers
    }
    out: Dict[str, List[ModelRef]] = {}
    for role, chain_raw in raw.items():
        if not isinstance(chain_raw, list):
            continue
        valid: List[ModelRef] = []
        for item in chain_raw:
            ref = _parse_model_ref(item)
            if ref is None:
                continue
            if ref.provider not in index:
                continue
            if ref.model not in index[ref.provider]:
                continue
            valid.append(ref)
        if valid:
            out[str(role)] = valid
    return out
