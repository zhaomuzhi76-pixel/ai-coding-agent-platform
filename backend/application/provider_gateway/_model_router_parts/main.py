"""Main class ModelRouter."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class ModelRouter(_Mixin1, _Mixin2):

    """Route LLM calls by task_type from yaml agent_routing.

    Responsibility:
        - 从配置中心读「角色 → 模型链」
        - 支持用户覆盖（override_model）
        - 逐个候选尝试直到成功

    Not Responsible:
        - actual model call (that is the gateway)
        - prompt building
    """
    VERSION = "2.0"
    RESPONSIBILITY = ("llm_task_routing_from_config",)
