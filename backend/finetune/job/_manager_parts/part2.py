"""Part 2 of manager.py."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (Callable, JobEvent, JobRecord, JobRunner, JobSpec, JobState, OnEvent, _store, asyncio, create_job_record, is_terminal,)  # noqa

class JobManager:
    VERSION = "1.0"

    def __init__(self, runner: JobRunner | None = None) -> None:
        self._runner = runner or JobRunner()
        self._tasks: dict[str, asyncio.Task] = {}
        self._records: dict[str, JobRecord] = {}
        self._listeners: list[OnEvent] = []

    # ── 提交 ──
    def submit(self, spec: JobSpec, *, spawn: bool | None = None) -> JobRecord:
        """创建任务记录 + 落盘。

        智能调度：
          - 有 running loop（FastAPI async 路由内）→ 自动 spawn 后台 task
          - 无 running loop（同步/测试/重放）→ 只落盘，返回 record；
            调用方可在 async 环境里用 await mgr.start(job_id) 手动启动

        spawn 参数：
          - None（默认）→ 自动判定
          - True → 强制 spawn（无 loop 时抛 RuntimeError）
          - False → 强制不 spawn
        """
        if not isinstance(spec, JobSpec):
            raise TypeError("spec must JobSpec")

        record = create_job_record(spec)
        self._records[record.job_id] = record
        _store.save_job_record(record)
        _store.append_job_event(record.job_id, JobEvent(
            "created", {"job_id": record.job_id, "spec": spec.to_dict()},
        ))

        # 判定是否需要 spawn
        if spawn is None:
            try:
                loop = asyncio.get_running_loop()
                do_spawn = loop is not None
            except RuntimeError:
                do_spawn = False
        else:
            do_spawn = bool(spawn)
            if do_spawn:
                try:
                    asyncio.get_running_loop()
                except RuntimeError as exc:
                    raise RuntimeError(
                        "submit(spawn=True) 需在 running event loop 内调用；"
                        "同步环境请用 submit() 后 await mgr.start(job_id)"
                    ) from exc

        if do_spawn:
            self._spawn_task(record)
        return record

    def _spawn_task(self, record: JobRecord) -> None:
        async def _go() -> None:
            on_event = self._make_broadcast(record.job_id)
            try:
                await self._runner.run(record, on_event=on_event)
            except asyncio.CancelledError:
                pass
            finally:
                _store.save_job_record(record)
                self._tasks.pop(record.job_id, None)

        task = asyncio.create_task(_go())
        self._tasks[record.job_id] = task

    async def start(self, job_id: str) -> bool:
        """在 async 环境里启动已落盘但未 spawn 的任务。

        返回 True = 启动成功；False = 任务不存在 / 已终态 / 已在运行。
        """
        if not job_id or not job_id.strip():
            raise ValueError("job_id required")
        rec = self._records.get(job_id)
        if rec is None:
            rec = _store.load_job_record(job_id)
            if rec is None:
                return False
            self._records[job_id] = rec
        if rec.state != JobState.PENDING:
            return False
        if job_id in self._tasks and not self._tasks[job_id].done():
            return False
        self._spawn_task(rec)
        return True

    # ── 查询 ──
    def get(self, job_id: str) -> JobRecord | None:
        r = self._records.get(job_id)
        if r is not None:
            return r
        return _store.load_job_record(job_id)

    def list(self, state: str = "", limit: int = 50) -> list[dict]:
        return _store.list_job_records(state=state, limit=limit)

    def events(self, job_id: str, limit: int = 500) -> list[dict]:
        return _store.load_job_events(job_id, limit=limit)

    # ── 取消 ──
    async def cancel(self, job_id: str) -> bool:
        if not job_id or not job_id.strip():
            raise ValueError("job_id required")
        task = self._tasks.get(job_id)
        if task is None or task.done():
            # 尝试从 store 拿 record 判断
            r = self.get(job_id)
            if r and not is_terminal(r.state):
                _store.update_job_state(
                    job_id, JobState.CANCELLED,
                    finished_at=__import__("time").time(),
                    error="cancelled (not running)",
                )
                return True
            return False
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
        return True

    async def cancel_all(self) -> None:
        for jid in list(self._tasks.keys()):
            await self.cancel(jid)

    # ── 事件订阅 ──
    def subscribe(self, listener: OnEvent) -> Callable[[], None]:
        self._listeners.append(listener)
        def _unsub() -> None:
            try: self._listeners.remove(listener)
            except ValueError: pass
        return _unsub

    def _make_broadcast(self, job_id: str) -> OnEvent:
        async def _on_event(event: JobEvent) -> None:
            # 落盘
            try: _store.append_job_event(job_id, event)
            except Exception: pass
            # 同步 record 到 store
            try:
                rec = self._records.get(job_id)
                if rec is not None:
                    _store.save_job_record(rec)
            except Exception: pass
            # 广播
            for cb in list(self._listeners):
                try:
                    res = cb(event)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    swallow("finetune.job._manager_parts.part2:162", e)
        return _on_event

    def stats(self) -> dict:
        active = sum(1 for t in self._tasks.values() if not t.done())
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "in_memory": len(self._records),
            "active_tasks": active,
            "listeners": len(self._listeners),
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return self.stats()

_manager: JobManager | None = None

def get_job_manager() -> JobManager:
    global _manager
    if _manager is None:
        _manager = JobManager()
    return _manager
