"""Main class PlatformBinding."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class PlatformBinding(_Mixin1, _Mixin2):

    VERSION = "2.0"
    PREFIX = "/api/platform"
