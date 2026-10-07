"""Embedding 模型解析器：全项目唯一真理源（所有 embedding 模型名由此解析）"""
import os

# 项目默认（可被环境变量 / Model Registry 覆盖）
DEFAULT_EMBEDDING = "qwen3-embedding:4b"


def resolve_embedding_model(explicit: str = "") -> str:
    """解析顺序：显式传参 > 环境变量 > Registry 中 embedding 角色 > 默认值"""
    if explicit:
        return explicit
    env = os.environ.get("VECTOR_EMBEDDING_MODEL", "").strip()
    if env:
        return env
    try:
        from .registry import get_registry
        reg = get_registry()
        # 优先 role='embedding' 的 primary
        route = reg.roles.get("embedding")
        if route and route.primary:
            return route.primary
        # 其次扫所有模型 id 含 embed 的
        for m in reg.models.values():
            if "embed" in m.id.lower():
                return m.id
    except Exception:
        pass
    return DEFAULT_EMBEDDING


def resolve_ollama_embed_url() -> str:
    """本地 Ollama embedding 端点（从 Registry 读，兜底 127.0.0.1:11434）"""
    try:
        from .registry import get_registry
        reg = get_registry()
        for p in reg.providers.values():
            if p.kind in ("ollama", "local", "ollama-local"):
                return p.base_url.rstrip("/")
    except Exception:
        pass
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
