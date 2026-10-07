"""TreeStreamer: NDJSON 流式输出。

契约：
  - async generator 逐行 yield
  - 每行 = 一帧 {type, seq, ...}
  - 帧类型：header（总数）/ entry（每项）/ footer（结束）
  - 允许"生产者推送"（entries 可来自异步回调）

不负责：
  - 分页逻辑（cursor 管）
  - 磁盘扫描 / 过滤 / 缓存
  - HTTP / WS 传输（调用方包）
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import AsyncIterator, Awaitable, Callable, Iterable


StreamLine = bytes


@dataclass(frozen=True, slots=True)
class StreamFrame:
    type: str
    seq: int
    payload: dict

    def to_bytes(self) -> bytes:
        obj = {"type": self.type, "seq": self.seq}
        obj.update(self.payload)
        text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        return (text + chr(10)).encode("utf-8")


class TreeStreamer:
    VERSION = "1.0"

    def __init__(self, path: str = "", chunk_size: int = 200) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        self.path = str(path)
        self.chunk_size = int(chunk_size)

    async def stream(
        self,
        entries: Iterable[dict],
        total: int | None = None,
        producer: Callable[[], Awaitable[list[dict] | None]] | None = None,
    ) -> AsyncIterator[StreamLine]:
        """两种用法：
          1) 传 entries 一次性流（大列表自动分块）
          2) 传 producer 回调 → 每帧从 producer 拉一批（支持增量/远程）
        """
        seq = 0
        emitted = 0
        if total is None:
            entries_list = list(entries)
            total = len(entries_list)
        else:
            entries_list = list(entries) if producer is None else []

        yield StreamFrame(
            type="header", seq=seq,
            payload={"path": self.path, "total": int(total)},
        ).to_bytes()
        seq += 1

        if producer is None:
            for e in entries_list:
                yield StreamFrame(
                    type="entry", seq=seq, payload={"entry": e},
                ).to_bytes()
                seq += 1
                emitted += 1
        else:
            while True:
                batch = await producer()
                if not batch:
                    break
                for e in batch:
                    yield StreamFrame(
                        type="entry", seq=seq, payload={"entry": e},
                    ).to_bytes()
                    seq += 1
                    emitted += 1

        yield StreamFrame(
            type="footer", seq=seq,
            payload={"emitted": emitted, "total": int(total)},
        ).to_bytes()

    def ready(self) -> bool:
        return self.chunk_size >= 1

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "path": self.path,
            "chunk_size": self.chunk_size,
            "ready": self.ready(),
        }


__all__ = ["TreeStreamer", "StreamFrame", "StreamLine"]
