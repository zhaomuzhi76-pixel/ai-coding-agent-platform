"""Main class CostTracker."""
from ._header import Any, CallRecord, Dict, List, Optional, Tuple, _agg_bucket, _finalize, _percentile, annotations, defaultdict, is_local_provider, time
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2
from .helpers import _percentile, _agg_bucket, _finalize

class CostTracker(_Mixin1, _Mixin2):
    VERSION = "2.0"
    MAX_RECORDS = 20000
