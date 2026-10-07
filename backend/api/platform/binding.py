"""PlatformBinding: HTTP-level binding for CodingPlatform.

支持 lazy platform：首次调用时才从 runtime deps 构造，
避免 router 装配时 bootstrap 还没跑的时序问题。
\n\nCompat shim. See ._binding_parts."""
from __future__ import annotations
from ._binding_parts import *  # noqa
from ._binding_parts import (PlatformBinding,)  # noqa
