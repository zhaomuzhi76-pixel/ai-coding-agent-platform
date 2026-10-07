"""ModelRouter: 从 llm_providers.yaml 的 agent_routing 读模型链。

用户前端可选「总模型」覆盖所有角色。
无配置时抛错——不再硬编码模型名。
\n\nCompat shim. See ._model_router_parts."""
from __future__ import annotations
from ._model_router_parts import *  # noqa
from ._model_router_parts import (ModelRouter,)  # noqa
