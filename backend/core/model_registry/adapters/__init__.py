"""框架适配层 - 每个框架一个独立文件，无业务逻辑，按需导入"""
__all__ = []

try:
    from .fastapi_adapter import build_router, mount
    __all__ = ["build_router", "mount"]
except ImportError:
    # FastAPI 未安装时静默跳过，不影响主架构
    pass
