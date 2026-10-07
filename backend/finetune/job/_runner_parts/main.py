"""Main class JobRunner."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2
from .mixin3 import _Mixin3

class JobRunner(_Mixin1, _Mixin2, _Mixin3):
    VERSION = "1.0"
