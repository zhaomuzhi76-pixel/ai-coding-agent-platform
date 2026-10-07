"""HF TrainerCallback：把每步/每次 log 转成 dict 投给线程安全 sink。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any, Callable, Optional

try:
    from transformers import TrainerCallback
except ImportError:
    TrainerCallback = object  # type: ignore


def _pick_loss(logs: Optional[dict]) -> float:
    if not logs:
        return 0.0
    for k in ("loss", "train_loss", "training_loss"):
        if k in logs and logs[k] is not None:
            try:
                return float(logs[k])
            except (TypeError, ValueError):
                continue
    return 0.0


def _pick_lr(logs: Optional[dict], state: Any = None) -> float:
    if logs:
        for k in ("learning_rate", "lr"):
            if k in logs and logs[k] is not None:
                try:
                    return float(logs[k])
                except (TypeError, ValueError):
                    continue
    # transformers 5.x 兜底：state 上挂着当前 lr
    if state is not None:
        v = getattr(state, "learning_rate", None)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return 0.0


class ProgressCallback(TrainerCallback):  # type: ignore[misc]
    """on_step_end + on_log 双通道：每步都推，loss 尽量从 logs 取。"""

    def __init__(self, sink: Callable[[dict], None],
                 fallback_lr: float = 0.0) -> None:
        self._sink = sink
        self._last = None
        self._fallback_lr = float(fallback_lr or 0.0)

    def _emit(self, state: Any, logs: Optional[dict]) -> None:
        payload = {
            "step": int(getattr(state, "global_step", 0) or 0),
            "total": int(getattr(state, "max_steps", 0) or 0),
            "loss": _pick_loss(logs),
            "lr": _pick_lr(logs, state) or getattr(self, "_fallback_lr", 0.0),
            "epoch": float(getattr(state, "epoch", 0.0) or 0.0),
        }
        if payload == self._last:
            return
        self._last = payload
        try:
            self._sink(payload)
        except Exception as e:
            swallow("finetune.backends.trainer_progress_callback:67", e)

    def on_step_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:
        self._emit(state, getattr(state, "log_history", [{}])[-1] if getattr(state, "log_history", None) else None)

    def on_log(self, args: Any, state: Any, control: Any,
               logs: Optional[dict] = None, **kwargs: Any) -> None:
        self._emit(state, logs)


__all__ = ["ProgressCallback"]
