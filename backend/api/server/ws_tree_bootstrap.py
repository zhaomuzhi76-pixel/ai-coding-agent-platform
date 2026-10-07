"""WSTreeBootstrap: /ws/tree 路由注册边界。

契约：
  - build(app) → 注册路由（幂等）
  - stop(app) → 卸载路由
  - 不持有连接状态（连接生命周期由 ws_tree.py 自管）

不负责：
  - 事件推送实现
  - 文件树 HTTP API
  - agent 通道
"""
from __future__ import annotations

from backend.api.ws_tree import PATH, register_ws_tree


class WSTreeBootstrap:
    VERSION = "1.0"

    def build(self, app) -> None:
        if app is None:
            raise ValueError("application required")
        register_ws_tree(app)

    def stop(self, app) -> None:
        if app is None:
            return
        routes = getattr(getattr(app, "router", None), "routes", ()) or ()
        app.router.routes[:] = [
            r for r in routes if getattr(r, "path", None) != PATH
        ]

    def registered(self, app) -> bool:
        if app is None:
            return False
        return any(
            getattr(r, "path", None) == PATH
            for r in (getattr(getattr(app, "router", None), "routes", ()) or ())
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "path": PATH,
            "ready": self.ready(),
        }


__all__ = ["WSTreeBootstrap"]
