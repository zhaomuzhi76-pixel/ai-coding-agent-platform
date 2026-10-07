"""Alert: rule + manager + in-memory sink."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

_SEVERITIES = ("info", "warning", "critical")


@dataclass(frozen=True)
class AlertRule:
    name: str
    severity: str
    description: str
    check: Callable[[Dict[str, Any]], bool]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("rule.name required")
        if self.severity not in _SEVERITIES:
            raise ValueError(f"severity must {_SEVERITIES}")
        if not callable(self.check):
            raise TypeError("rule.check must callable")


@dataclass
class AlertEvent:
    rule: str
    severity: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    alert_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "context": dict(self.context),
            "created_at": self.created_at,
        }

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


class AlertManager:
    """Evaluate rules against a snapshot; emit AlertEvent on trigger."""

    VERSION = "1.0"

    def __init__(self) -> None:
        self._rules: Dict[str, AlertRule] = {}
        self._events: List[AlertEvent] = []

    def register(self, rule: AlertRule) -> None:
        self._rules[rule.name] = rule

    def register_all(self, rules: List[AlertRule]) -> None:
        for r in rules:
            self.register(r)

    def names(self) -> List[str]:
        return sorted(self._rules.keys())

    def evaluate(
        self, snapshot: Dict[str, Any],
    ) -> List[AlertEvent]:
        fired: List[AlertEvent] = []
        for rule in self._rules.values():
            try:
                if rule.check(snapshot):
                    evt = AlertEvent(
                        rule=rule.name,
                        severity=rule.severity,
                        message=rule.description,
                        context={"snapshot_keys": sorted(snapshot.keys())},
                    )
                    self._events.append(evt)
                    fired.append(evt)
            except Exception:
                continue
        return fired

    def events(self) -> List[AlertEvent]:
        return list(self._events)

    def by_severity(self, severity: str) -> List[AlertEvent]:
        return [e for e in self._events if e.severity == severity]

    def clear(self) -> None:
        self._events.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "rules": self.names(),
            "events": len(self._events),
        }


def latency_p95_over(threshold_ms: float, span_name: str = "") -> AlertRule:
    """Trigger when p95 latency exceeds threshold."""
    def _check(snapshot: Dict[str, Any]) -> bool:
        tracer = snapshot.get("tracer")
        if tracer is None:
            return False
        return tracer.percentile(95, span_name or None) > threshold_ms
    return AlertRule(
        name=f"p95>{int(threshold_ms)}ms",
        severity="warning",
        description=(
            f"p95 latency exceeded {threshold_ms}ms"
            + (f" for {span_name}" if span_name else "")
        ),
        check=_check,
    )


def error_rate_over(
    threshold: float, window: int = 100,
) -> AlertRule:
    """Trigger when recent error rate exceeds threshold (0..1)."""
    def _check(snapshot: Dict[str, Any]) -> bool:
        tracer = snapshot.get("tracer")
        if tracer is None:
            return False
        spans = tracer.spans()[-window:]
        if not spans:
            return False
        errs = sum(1 for s in spans if s.status == "error")
        return (errs / len(spans)) > threshold
    return AlertRule(
        name=f"error_rate>{threshold}",
        severity="critical",
        description=f"error rate over {threshold} in last {window} spans",
        check=_check,
    )


def failure_count_over(threshold: int) -> AlertRule:
    """Trigger when metrics.failure_count exceeds threshold."""
    def _check(snapshot: Dict[str, Any]) -> bool:
        metrics = snapshot.get("metrics") or {}
        value = metrics.get("failure_count", 0)
        try:
            return int(value) > threshold
        except (TypeError, ValueError):
            return False
    return AlertRule(
        name=f"failure_count>{threshold}",
        severity="warning",
        description=f"failure_count exceeded {threshold}",
        check=_check,
    )


__all__ = [
    "AlertRule",
    "AlertEvent",
    "AlertManager",
    "latency_p95_over",
    "error_rate_over",
    "failure_count_over",
]
