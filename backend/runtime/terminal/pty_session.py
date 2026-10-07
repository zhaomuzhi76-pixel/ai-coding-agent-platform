"""PTY 会话：在本地启动 shell，双向转发字节流。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import os
import pty
import signal
import struct
import fcntl
import termios
from typing import Callable, Optional


class PtySession:
    """管理一个本地 PTY + 子进程。"""

    def __init__(
        self,
        on_output: Callable[[bytes], None],
        shell: Optional[str] = None,
    ) -> None:
        self._on_output = on_output
        self._shell = shell or os.environ.get("SHELL", "/bin/bash")
        self._master_fd: Optional[int] = None
        self._child_pid: Optional[int] = None
        self._closed = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        self._loop = loop

        master_fd, slave_fd = pty.openpty()
        self._master_fd = master_fd

        pid = os.fork()
        if pid == 0:
            # 子进程
            os.close(master_fd)
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            if slave_fd > 2:
                os.close(slave_fd)
            os.execvp(self._shell, [self._shell, "-l"])
            os._exit(1)

        os.close(slave_fd)
        self._child_pid = pid

        # 非阻塞
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        loop.add_reader(master_fd, self._read_ready)

    def _read_ready(self) -> None:
        if self._master_fd is None or self._closed:
            return
        try:
            data = os.read(self._master_fd, 8192)
        except (BlockingIOError, InterruptedError):
            return
        except OSError:
            self.close()
            return
        if not data:
            self.close()
            return
        try:
            self._on_output(data)
        except Exception as e:
            swallow("runtime.terminal.pty_session:75", e)

    def write(self, data: bytes) -> None:
        if self._master_fd is None or self._closed:
            return
        try:
            os.write(self._master_fd, data)
        except OSError:
            self.close()

    def resize(self, cols: int, rows: int) -> None:
        if self._master_fd is None or self._closed:
            return
        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, winsize)
        except OSError:
            pass

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        loop = self._loop
        if self._master_fd is not None:
            try:
                if loop:
                    loop.remove_reader(self._master_fd)
            except Exception as e:
                swallow("runtime.terminal.pty_session:104", e)
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None
        if self._child_pid:
            try:
                os.kill(self._child_pid, signal.SIGHUP)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(self._child_pid, os.WNOHANG)
            except ChildProcessError:
                pass
            self._child_pid = None
