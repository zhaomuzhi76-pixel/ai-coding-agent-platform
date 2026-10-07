"""Mixin 2 of JobRunner."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (Any, FinetuneConfig, JobRecord, JobState, OnEvent, asyncio, build_config, cancelled_event, failed_event, log_event, progress_event, started_event, succeeded_event, time, validate_transition,)  # noqa: F401
class _Mixin2:
    async def run(
        self,
        record: JobRecord,
        on_event: OnEvent | None = None,
    ) -> JobRecord:
        """执行一个任务（阻塞直到完成/失败/取消）。"""
        spec = record.spec
        # pending → running
        try:
            validate_transition(record.state, JobState.RUNNING)
        except ValueError as exc:
            await self._emit(on_event, failed_event(record.job_id, str(exc)))
            record.state = JobState.FAILED
            record.error = str(exc)
            return record

        record.state = JobState.RUNNING
        record.started_at = time.time()
        record.touch()
        await self._emit(on_event, started_event(record.job_id))

        try:
            # 构造 FinetuneConfig
            cfg: FinetuneConfig = build_config(
                spec.recipe_name, spec.base_model,
            )
            # 训练参数覆盖（JobSpec 优先于 recipe 默认）
            _ov = {}
            if getattr(spec, "num_epochs", 0) > 0:
                _ov["num_epochs"] = int(spec.num_epochs)
            if getattr(spec, "batch_size", 0) > 0:
                _ov["batch_size"] = int(spec.batch_size)
            if getattr(spec, "learning_rate", 0.0) > 0:
                _ov["learning_rate"] = float(spec.learning_rate)
            if getattr(spec, "max_seq_len", 0) > 0:
                _ov["max_seq_len"] = int(spec.max_seq_len)
            if _ov:
                import dataclasses as _dc
                if _dc.is_dataclass(cfg):
                    cfg = _dc.replace(cfg, **_ov)
                else:
                    for _k, _v in _ov.items():
                        try: setattr(cfg, _k, _v)
                        except Exception: pass
            # ⚠️ D5 扫描约定：adapter 必须落 <base>/adapter/ 子目录
            # 否则 scan_local_adapters 找不到
            from pathlib import Path as _P
            if spec.output_dir:
                cfg.output_dir = str(_P(spec.output_dir) / "adapter")
            else:
                cfg.output_dir = str(
                    _P.home() / ".biancheng" / "finetune"
                    / record.job_id / "adapter"
                )

            # 数据加载
            from backend.finetune.data.loader import load_jsonl_clean
            try:
                samples = load_jsonl_clean(spec.dataset_path)
            except Exception as exc:
                await self._emit(
                    on_event,
                    log_event(record.job_id,
                              f"数据加载失败: {exc}", level="error"),
                )
                raise

            total = len(samples)
            record.total_steps = total
            await self._emit(
                on_event,
                log_event(record.job_id,
                          f"加载 {total} 条样本，开始训练",
                          level="info"),
            )
            if total == 0:
                raise ValueError("dataset empty")

            # 训练（同步 backend → to_thread）
            from backend.finetune.trainer import FinetuneTrainer
            trainer = FinetuneTrainer(cfg, backend=self._backend_override)
            if not trainer.available():
                raise RuntimeError(
                    f"backend not available: {trainer.backend.name} "
                    f"(需要安装 peft/transformers)"
                )

            import queue as _q
            _loop = asyncio.get_running_loop()
            _pq: _q.Queue = _q.Queue(maxsize=2000)

            def _sink(payload: dict) -> None:
                try:
                    _loop.call_soon_threadsafe(_pq.put_nowait, payload)
                except Exception as e:
                    swallow("finetune.job._runner_parts.mixin2:102", e, level="error")

            async def _drain() -> None:
                while True:
                    try:
                        p = _pq.get_nowait()
                    except _q.Empty:
                        await asyncio.sleep(0.05)
                        continue
                    if p.get("_end"):
                        return
                    try:
                        st = int(p.get("step", 0))
                        tt = int(p.get("total", 0)) or getattr(record, "total_steps", 0)
                        ls = float(p.get("loss", 0.0))
                        # 回写 record（让最终 GET /jobs/{id} 也有真实 loss）
                        try:
                            if tt > 0:
                                record.total_steps = tt
                            if st > 0:
                                record.current_step = st
                            if tt > 0:
                                record.progress = round(st / tt * 100.0, 2)
                            if ls > 0:
                                record.loss = ls
                            _store.save_job_record(record)
                        except Exception as e:
                            swallow("finetune.job._runner_parts.mixin2:129", e, level="error")
                        await self._emit(
                            on_event,
                            progress_event(
                                record.job_id, st, tt,
                                loss=ls,
                                lr=float(p.get("lr", 0.0)),
                                epoch=float(p.get("epoch", 0.0)),
                            ),
                        )
                    except Exception as e:
                        swallow("finetune.job._runner_parts.mixin2:140", e, level="error")

            _drain_task = asyncio.create_task(_drain())

            def _do_train() -> Any:
                try:
                    return trainer.train(samples, on_progress=_sink)
                finally:
                    try:
                        _loop.call_soon_threadsafe(
                            _pq.put_nowait, {"_end": True},
                        )
                    except Exception as e:
                        swallow("finetune.job._runner_parts.mixin2:153", e, level="error")

            report = await asyncio.to_thread(_do_train)
            # stub backend 会抛 NotImplementedError → 转 RuntimeError
            if not report.ok:
                raise RuntimeError(
                    report.error or "training failed"
                )

            record.saved_to = report.saved_to
            record.progress = 100.0
            record.current_step = total
            record.finished_at = time.time()
            record.state = JobState.SUCCEEDED
            record.touch()

            # 训练成功 → 自动注册 adapter（省用户手动 scan）
            await self._emit(
                on_event,
                succeeded_event(record.job_id, saved_to=record.saved_to),
            )

            # ── 训练成功 → 自动注册 adapter（同步；_run_sync 已在 to_thread 里）──
            try:
                from pathlib import Path as _P
                from backend.finetune.deploy.registry import scan_local_adapters
                _saved = str(getattr(record, "saved_to", "") or "")
                if _saved:
                    _adapter_dir = _P(_saved)
                    if (_adapter_dir / "adapter_config.json").is_file():
                        scan_local_adapters(
                            root=_adapter_dir.parent.parent, register=True,
                        )
            except Exception as e:
                swallow("finetune.job._runner_parts.mixin2:187", e, level="error")

        except asyncio.CancelledError:
            record.finished_at = time.time()
            record.state = JobState.CANCELLED
            record.error = "cancelled by user"
            record.touch()
            await self._emit(on_event, cancelled_event(record.job_id))
            raise

        except Exception as exc:
            record.finished_at = time.time()
            record.state = JobState.FAILED
            record.error = f"{type(exc).__name__}: {exc}"
            record.touch()
            await self._emit(
                on_event,
                failed_event(record.job_id, record.error),
            )

        return record
