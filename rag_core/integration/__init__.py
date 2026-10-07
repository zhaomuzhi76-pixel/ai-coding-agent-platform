# 职责：RAG 嵌入式集成的对外契约入口
from .mount import mount_rag
from .bridge import get_bridge

__all__ = ["mount_rag", "get_bridge"]
