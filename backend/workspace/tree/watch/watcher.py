"""TreeWatcher: 轮询式目录监控（零依赖）。

契约：
  - register(path) 注册监控目录
  - poll_once() → 返回 [WatchEvent]
  - start()/stop() 后台轮询（asyncio task）
  - 事件类型：created / deleted / modified
  - 内部维护 {path: {name: (mtime_ns, size, kind)}}

不负责：
  - WS / HTTP 传输
  - 过滤（filter 层管）
  - 缓存（index 层管）
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Awaitable


MIN_INTERVAL_SEC = 0.5


@dataclass(frozen=True, slots=True)
class WatchEvent:
    type: str          # created / modified / deleted
    path: str          # 相对根路径
    name: str
    kind: str          # dir / file
    mtime_ns: int = 0
    size: int = 0

    def to_dict(self) -> dict:
        return {
            "type": self.type, "path": self.path, "name": self.name,
            "kind": self.kind, "mtime_ns": self.mtime_ns, "size": self.size,
        }


@dataclass
class WatchSnapshot:
    children: dict = field(default_factory=dict)   # name -> (mtime_ns, size, kind)
    missing: bool = False


class TreeWatcher:
    VERSION = "1.0"

    def __init__(
        self,
        root: Path,
        interval_sec: float = 2.0,
    ) -> None:
        if not isinstance(root, Path):
            raise TypeError("root must be Path")
        if interval_sec < MIN_INTERVAL_SEC:
            raise ValueError(f"interval_sec must be >= {MIN_INTERVAL_SEC}")
        self.root = root
        self.interval_sec = float(interval_sec)
        self._dirs: set[str] = set()
        self._snap: dict[str, WatchSnapshot] = {}
        self._task: asyncio.Task | None = None
        self._stop = False
        self.polls = 0
        self.events_emitted = 0

    def register(self, rel_path: str = "") -> None:
        self._dirs.add(rel_path)

    def unregister(self, rel_path: str) -> None:
        self._dirs.discard(rel_path)
        self._snap.pop(rel_path, None)

    def poll_once(self) -> list[WatchEvent]:
        """同步扫描全部注册目录，返回事件列表。"""
        self.polls += 1
        out: list[WatchEvent] = []
        for rel in list(self._dirs):
            out.extend(self._diff_dir(rel))
        self.events_emitted += len(out)
        return out

    async def start(
        self,
        on_events: Callable[[list[WatchEvent]], Awaitable[None]] | None = None,
    ) -> None:
        if self._task is not None:
            return
        self._stop = False
        self._task = asyncio.create_task(self._loop(on_events))

    async def stop(self) -> None:
        self._stop = True
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
            self._task = None

    def ready(self) -> bool:
        return self.root.exists() and self.interval_sec >= MIN_INTERVAL_SEC

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "root": str(self.root),
            "dirs": len(self._dirs),
            "interval_sec": self.interval_sec,
            "polls": self.polls,
            "events_emitted": self.events_emitted,
            "ready": self.ready(),
        }

    # ── 内部 ──
    def _snapshot_dir(self, rel: str) -> WatchSnapshot:
        target = self.root / rel if rel else self.root
        try:
            entries = list(os.scandir(target))
        except FileNotFoundError:
            return WatchSnapshot({}, missing=True)
        except OSError:
            return WatchSnapshot({}, missing=True)
        children: dict = {}
        for e in entries:
            try:
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            kind = "dir" if e.is_dir(follow_symlinks=False) else "file"
            children[e.name] = (int(st.st_mtime_ns), int(st.st_size), kind)
        return WatchSnapshot(children, missing=False)

    def _diff_dir(self, rel: str) -> list[WatchEvent]:
        now = self._snapshot_dir(rel)
        prev = self._snap.get(rel)
        self._snap[rel] = now
        if prev is None:
            return []  # 首次 = 初始化，不报事件
        if now.missing:
            if prev.missing:
                return []
            return [WatchEvent("deleted", rel, "", "dir")]

        events: list[WatchEvent] = []
        for name, meta in now.children.items():
            child_rel = (rel + "/" + name).strip("/") if rel else name
            if name not in prev.children:
                events.append(WatchEvent(
                    "created", child_rel, name, meta[2], meta[0], meta[1],
                ))
            else:
                pm = prev.children[name]
                if pm[0] != meta[0] or pm[1] != meta[1]:
                    events.append(WatchEvent(
                        "modified", child_rel, name, meta[2], meta[0], meta[1],
                    ))
        for name, pm in prev.children.items():
            if name not in now.children:
                child_rel = (rel + "/" + name).strip("/") if rel else name
                events.append(WatchEvent("deleted", child_rel, name, pm[2]))
        return events

    async def _loop(
        self,
        on_events: Callable[[list[WatchEvent]], Awaitable[None]] | None,
    ) -> None:
        while not self._stop:
            try:
                events = self.poll_once()
                if events and on_events is not None:
                    await on_events(events)
            except asyncio.CancelledError:
                return
            except Exception as e:
                swallow("workspace.tree.watch.watcher:180", e)
            await asyncio.sleep(self.interval_sec)


__all__ = ["TreeWatcher", "WatchEvent", "WatchSnapshot", "MIN_INTERVAL_SEC"]
