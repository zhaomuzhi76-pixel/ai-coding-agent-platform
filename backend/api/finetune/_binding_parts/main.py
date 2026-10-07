"""Main class FinetuneBinding."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class FinetuneBinding(_Mixin1, _Mixin2):

    VERSION = "1.0"
    PREFIX = "/api/finetune"
