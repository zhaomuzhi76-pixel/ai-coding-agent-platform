"""Agent 工作区模型目录端点（数据源统一为 Model Registry）"""
from .router import build_providers_catalog_router

__all__ = ["build_providers_catalog_router"]
