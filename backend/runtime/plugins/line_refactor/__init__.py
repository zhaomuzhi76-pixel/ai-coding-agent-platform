"""Line Refactor 插件：自动把超限模块拆成包。"""
from backend.runtime.plugins.line_refactor.capability import CAPABILITY
from backend.runtime.plugins.line_refactor.plugin import LineRefactorPlugin
from backend.runtime.plugins.line_refactor.provider import LineRefactorProvider

__all__ = ["CAPABILITY", "LineRefactorPlugin", "LineRefactorProvider"]
