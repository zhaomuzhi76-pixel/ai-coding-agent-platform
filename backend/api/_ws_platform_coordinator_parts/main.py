"""Main class PlatformBackedCoordinator."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class PlatformBackedCoordinator(_Mixin1, _Mixin2):

    VERSION = "1.0"
    EXECUTION_TIMEOUT = 600
