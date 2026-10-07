"""Subprocess stdio transport (client side): spawn MCP server process."""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import json
import shutil
from typing import Any, Dict, List, Optional

from backend.mcp.transport.base import Transport


class StdioClientTransport:
    """Spawns a subprocess and exchanges newline-delimited JSON over stdio."""

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        self._command = command
        self._args = list(args or [])
        self._env = env
        self._proc: Optional[asyncio.subprocess.Process] = None

    async def start(self) -> None:
        if shutil.which(self._command) is None:
            raise FileNotFoundError(f"command not found: {self._command}")
        self._proc = await asyncio.create_subprocess_exec(
            self._command, *self._args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
        )

    async def send(self, message: Dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("stdio transport not started")
        line = json.dumps(message, ensure_ascii=False) + "\n"
        self._proc.stdin.write(line.encode("utf-8"))
        await self._proc.stdin.drain()

    async def receive(self) -> Optional[Dict[str, Any]]:
        if self._proc is None or self._proc.stdout is None:
            return None
        line = await self._proc.stdout.readline()
        if not line:
            return None
        text = line.decode("utf-8").strip()
        if not text:
            return None
        return json.loads(text)

    async def close(self) -> None:
        if self._proc is None:
            return
        try:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
        except Exception as e:
            swallow("mcp.transport.stdio:63", e)
        try:
            self._proc.terminate()
            await asyncio.wait_for(self._proc.wait(), timeout=3.0)
        except Exception:
            try:
                self._proc.kill()
            except Exception as e:
                swallow("mcp.transport.stdio:71", e)
        self._proc = None

    def ready(self) -> bool:
        return self._proc is not None and self._proc.returncode is None


__all__ = ["StdioClientTransport"]
