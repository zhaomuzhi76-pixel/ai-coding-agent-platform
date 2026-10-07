"""PlatformBackedCoordinator: WS 请求 → PlatformBinding。

WS 请求 → platform 门面，不重造执行逻辑。
不重造执行逻辑，直接走 platform REST binding。
\n\nCompat shim. See ._ws_platform_coordinator_parts."""
from __future__ import annotations
from ._ws_platform_coordinator_parts import *  # noqa
from ._ws_platform_coordinator_parts import (PlatformBackedCoordinator,)  # noqa
