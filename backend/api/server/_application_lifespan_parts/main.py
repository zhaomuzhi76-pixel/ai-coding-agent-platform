"""Main class ApplicationLifespan."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class ApplicationLifespan(_Mixin1, _Mixin2):

    """
    Canonical FastAPI application lifespan boundary.

    Owns:
        - injected bootstrap lifecycle
        - startup orchestration delegation
        - active ApplicationStartup reference
        - startup rollback
        - shutdown orchestration delegation

    Does not own:
        - top-level bootstrap discovery
        - system construction
        - application construction
        - runtime construction
        - transport construction
    """
    VERSION = "1.4"
