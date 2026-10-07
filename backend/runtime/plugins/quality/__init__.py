"""Quality 插件：把 quality 层挂到 runtime，不做任何门禁逻辑。"""
from backend.runtime.plugins.quality.capability import CAPABILITY
from backend.runtime.plugins.quality.plugin import QualityPlugin
from backend.runtime.plugins.quality.provider import QualityProvider

__all__ = ["CAPABILITY", "QualityPlugin", "QualityProvider"]
