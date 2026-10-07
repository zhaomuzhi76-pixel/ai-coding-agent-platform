"""兼容 re-export —— 实际实现已提升到 backend/rag/recall_config.py。"""
from backend.rag.recall_config import (
    RecallConfig, RecallConfigStore, get_default_config,
)
__all__ = ["RecallConfig", "RecallConfigStore", "get_default_config"]
