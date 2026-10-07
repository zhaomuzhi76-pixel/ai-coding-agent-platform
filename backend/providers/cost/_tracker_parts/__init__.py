"""Auto-split. Do not edit."""
from . import _header as _m__header
from . import helpers as _m_helpers
from . import mixin1 as _m_mixin1
from . import mixin2 as _m_mixin2
from . import main as _m_main
_mods = (_m__header, _m_helpers, _m_mixin1, _m_mixin2, _m_main)
_ns = {}
for _m in _mods:
    for _k, _v in vars(_m).items():
        if not _k.startswith('__'): _ns[_k] = _v
for _m in _mods: vars(_m).update(_ns)
globals().update(_ns)
