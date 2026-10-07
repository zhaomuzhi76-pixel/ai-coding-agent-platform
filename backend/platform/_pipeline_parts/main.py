"""Main class PlatformPipeline."""
from __future__ import annotations
from .part1 import PipelinePhasesMixin  # noqa
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class PlatformPipeline(_Mixin1, _Mixin2, PipelinePhasesMixin):

    VERSION = "1.0"
