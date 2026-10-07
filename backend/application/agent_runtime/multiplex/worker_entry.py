"""子进程入口：读 IPC task → 执行 → 写 IPC step/result。

不变量：
  - env 在任何 backend import 之前设置
  - 不 import supervisor / registry
  - agent_entry 延迟到真跑任务时才 import
  - 所有输出强制带 session_id
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import os as _os
_os.environ.setdefault("LOCO_WORKER_ACTIVE", "1")
_os.environ.setdefault("LOCO_WORKER_POOL_SIZE", "0")

import asyncio
import sys
import uuid
from typing import Any

from . import protocol


def _write(msg: dict) -> None:
    sys.stdout.buffer.write(protocol.encode_message(msg))
    sys.stdout.buffer.flush()


def _log(text: str) -> None:
    sys.stderr.write("[multiplex.worker] " + text + chr(10))
    sys.stderr.flush()


async def _run_task(msg: dict) -> None:
    session_id = msg["session_id"]
    task_id = msg["task_id"]

    def _emit_step(entry: dict) -> None:
        try:
            _write(protocol.make_step(
                session_id=session_id, task_id=task_id, entry=entry,
            ))
        except Exception as e:
            swallow("application.agent_runtime.multiplex.worker_entry:44", e)

    try:
        from backend.application.agent_entry import dispatch
        gateway = _build_gateway()
        payload = {
            "message": str(msg.get("message", "")),
            "workspace": str(msg.get("workspace", "")),
            "provider": str(msg.get("provider", "")),
            "model": str(msg.get("model", "")),
            "base_url": str(msg.get("base_url", "")),
            "api_key": str(msg.get("api_key", "")),
        }
        result = await dispatch(
            payload, session=None, gateway=gateway, on_step=_emit_step,
        )
        _write(protocol.make_result(
            session_id=session_id, task_id=task_id,
            result=result if result is not None else {},
        ))
    except Exception as exc:
        import traceback
        traceback.print_exc(file=sys.stderr)
        try:
            _write(protocol.make_error(
                session_id=session_id, task_id=task_id,
                error=type(exc).__name__ + ": " + str(exc),
            ))
        except Exception as e:
            swallow("application.agent_runtime.multiplex.worker_entry:73", e)


def _build_gateway() -> Any:
    """从配置构造 gateway（与主进程同一路径）。

    主进程：ApplicationBootstrapCompositionFactory.create() L83-94
    子进程：照抄 4 行，无父进程状态依赖（ModelRouter 只读 YAML）。
    """
    try:
        from backend.providers.assembly.configuration import (
            ProviderAssemblyConfiguration,
        )
        from backend.providers.assembly.builder import (
            ProviderAssemblyBuilder,
        )
        from backend.providers.assembly.runtime_factory import (
            ProviderAssemblyRuntimeFactory,
        )
        from backend.application.provider_gateway.gateway import (
            ApplicationProviderGateway,
        )
    except Exception as exc:
        _log("gateway import failed: " + type(exc).__name__ + ": " + str(exc))
        return None

    try:
        provider_context = (
            ProviderAssemblyBuilder(
                configuration=ProviderAssemblyConfiguration()
            ).build()
        )
        provider_runtime = (
            ProviderAssemblyRuntimeFactory().create(provider_context)
        )
        return ApplicationProviderGateway(provider_runtime)
    except Exception as exc:
        import traceback
        traceback.print_exc(file=sys.stderr)
        _log("gateway build failed: " + type(exc).__name__ + ": " + str(exc))
        return None


async def _main() -> None:
    worker_id = "mpx-" + uuid.uuid4().hex[:8]
    _write(protocol.make_ready(worker_id))
    _log(worker_id + " ready")

    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    stream_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: stream_protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break
        try:
            msg = protocol.decode_message(line)
        except protocol.ProtocolError as exc:
            _log("protocol error: " + str(exc))
            continue
        if msg is None:
            continue
        mtype = msg.get("type")
        if mtype == protocol.MSG_SHUTDOWN:
            _log(worker_id + " shutdown")
            return
        if mtype == protocol.MSG_PING:
            _write(protocol.make_pong())
            continue
        if mtype == protocol.MSG_TASK:
            await _run_task(msg)
            continue
        _log("unknown type: " + repr(mtype))


def main() -> None:
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


__all__ = ["main"]
