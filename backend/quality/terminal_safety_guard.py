"""禁止终端退出守卫：拦截 sys.exit / os._exit。"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Iterator, List


class TerminalExitDetected(RuntimeError):
    pass


@contextmanager
def no_terminal_exit() -> Iterator[List[str]]:
    recorded: List[str] = []
    real_sys_exit = sys.exit
    real_os_exit = os._exit

    def guarded_sys_exit(code=0):
        recorded.append("sys.exit")
        raise TerminalExitDetected(f"sys.exit({code}) blocked")

    def guarded_os_exit(code=0):
        recorded.append("os._exit")
        raise TerminalExitDetected(f"os._exit({code}) blocked")

    sys.exit = guarded_sys_exit
    os._exit = guarded_os_exit
    try:
        yield recorded
    finally:
        sys.exit = real_sys_exit
        os._exit = real_os_exit
