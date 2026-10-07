"""Main class PrefixTuningBackend."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class PrefixTuningBackend(_Mixin1, _Mixin2):

    name = "prefix"
