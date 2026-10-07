"""Auto-split parts. Do not edit."""
from . import _header as _h
from . import part1 as _p1
from . import part2 as _p2
_mods = (_h, _p1, _p2)
_ns = {}
for _m in _mods:
    for _k, _v in vars(_m).items():
        if not _k.startswith('__'): _ns[_k] = _v
for _m in _mods: vars(_m).update(_ns)
globals().update(_ns)
