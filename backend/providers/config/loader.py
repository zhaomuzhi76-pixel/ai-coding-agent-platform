"""Load LLM provider config from YAML with env substitution.

职责：
    - 读 YAML
    - ${VAR} 环境变量替换
    - 缺 API key 的 provider 自动跳过（本地优先）
    - 校验结构
    - 读 agent_routing（角色 → 模型链）
\n\nCompat shim. See ._loader_parts."""
from __future__ import annotations
from ._loader_parts import *  # noqa
from ._loader_parts import (Any, Dict, EmbeddingSpec, LLMConfig, List, ModelRef, ModelSpec, Optional, Path, ProviderSpec, RerankerSpec, VectorStoreSpec, _DEFAULT_PATH, _ENV_FILE, _ENV_RE, _PROJECT_ROOT, _REQUIRE_KEY, __all__, _load_dotenv, _parse_embedding, _parse_model, _parse_model_ref, _parse_provider, _parse_reranker, _parse_routing, _parse_vector_store, _substitute_env, annotations, dataclass, field, load_llm_config, os, re, yaml,)  # noqa
