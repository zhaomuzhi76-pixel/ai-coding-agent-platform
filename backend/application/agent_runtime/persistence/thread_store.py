"""ThreadStore: Thread/Turn/Item 三级 MongoDB 持久化。

契约：
    - 三级集合（threads / turns / items）
    - 每次写操作 upsert（幂等）
    - 支持跨进程读取（状态可恢复）
    - 索引：thread_id / turn_id / session_id
"""
from __future__ import annotations

from typing import Optional

from backend.application.agent_runtime.contracts import (
    Item, Thread, Turn,
)


class ThreadStore:
    VERSION = "1.0"

    COLL_THREADS = "agent_threads"
    COLL_TURNS = "agent_turns"
    COLL_ITEMS = "agent_items"

    def __init__(self, database) -> None:
        self._db = database

    @property
    def threads(self):
        return self._db[self.COLL_THREADS]

    @property
    def turns(self):
        return self._db[self.COLL_TURNS]

    @property
    def items(self):
        return self._db[self.COLL_ITEMS]

    async def save_thread(self, t: Thread) -> None:
        self.threads.replace_one(
            {"thread_id": t.thread_id},
            t.to_mongo(),
            upsert=True,
        )

    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        doc = self.threads.find_one({"thread_id": thread_id})
        return Thread.from_mongo(doc) if doc else None

    async def find_active_threads(self) -> list[Thread]:
        cursor = self.threads.find(
            {"status": {"$in": ["running", "waiting_approval"]}}
        )
        return [Thread.from_mongo(d) for d in cursor]

    async def find_by_session(self, session_id: str) -> list[Thread]:
        cursor = self.threads.find({"session_id": session_id}).sort(
            "created_at", -1,
        )
        return [Thread.from_mongo(d) for d in cursor]

    async def save_turn(self, t: Turn) -> None:
        self.turns.replace_one(
            {"turn_id": t.turn_id},
            t.to_mongo(),
            upsert=True,
        )

    async def get_turn(self, turn_id: str) -> Optional[Turn]:
        doc = self.turns.find_one({"turn_id": turn_id})
        return Turn.from_mongo(doc) if doc else None

    async def list_turns(self, thread_id: str) -> list[Turn]:
        cursor = self.turns.find(
            {"thread_id": thread_id}
        ).sort("index", 1)
        return [Turn.from_mongo(d) for d in cursor]

    async def append_item(self, it: Item) -> None:
        self.items.replace_one(
            {"item_id": it.item_id},
            it.to_mongo(),
            upsert=True,
        )

    async def list_items(self, turn_id: str) -> list[Item]:
        cursor = self.items.find(
            {"turn_id": turn_id}
        ).sort("created_at", 1)
        return [Item.from_mongo(d) for d in cursor]

    async def mark_orphaned(self, pid: int) -> int:
        """把指定 worker pid 的活跃 thread 标为 orphaned。"""
        r = self.threads.update_many(
            {"status": "running", "worker_pid": pid},
            {"$set": {"status": "orphaned"}},
        )
        return r.modified_count

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "collections": [
                self.COLL_THREADS,
                self.COLL_TURNS,
                self.COLL_ITEMS,
            ],
        }


__all__ = ["ThreadStore"]
