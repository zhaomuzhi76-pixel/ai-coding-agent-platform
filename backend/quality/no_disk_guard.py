"""禁止落盘守卫：拦截 builtins.open / os.open 的写操作。"""
from __future__ import annotations

import builtins
import os
from contextlib import contextmanager
from typing import Iterator, List


class DiskWriteDetected(RuntimeError):
    pass


_WRITE_MODES = {"w", "a", "x", "+"}


def _is_write_mode(mode: str) -> bool:
    return any(ch in mode for ch in _WRITE_MODES)


@contextmanager
def no_disk_writes() -> Iterator[List[str]]:
    recorded: List[str] = []
    real_open = builtins.open
    real_os_open = os.open

    def guarded_open(file, mode="r", *args, **kwargs):
        if _is_write_mode(mode):
            recorded.append(str(file))
            raise DiskWriteDetected(f"disk write blocked: {file}")
        return real_open(file, mode, *args, **kwargs)

    def guarded_os_open(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND):
            recorded.append(str(path))
            raise DiskWriteDetected(f"disk write blocked: {path}")
        return real_os_open(path, flags, *args, **kwargs)

    builtins.open = guarded_open
    os.open = guarded_os_open
    try:
        yield recorded
    finally:
        builtins.open = real_open
        os.open = real_os_open
