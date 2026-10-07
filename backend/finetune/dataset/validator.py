"""数据集内容校验（D4-L0 · 只读）。

职责：
    - 读 JSONL 文件，逐行校验
    - 返回结构化报告（通过 / 警告 / 错误 / 预览）
    - 统计样本数 + 字节大小

不负责：
    - 文件写入（storage 管）
    - 元数据（spec 管）
    - HTTP（api 管）

校验规则：
    - 每行必须是合法 JSON 对象
    - 必须含 "user" 和 "assistant" 字段（非空字符串）
    - "system" / "history" 可选
    - 空行 / "#" 注释行跳过
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MAX_PREVIEW_LINES = 3
MAX_ISSUES = 200

# 与 backend.finetune.data.preprocessor.filter_by_length 保持一致
MIN_SAMPLE_CHARS = 10
MAX_SAMPLE_CHARS = 8000


def _sample_char_count(data: dict) -> int:
    user = str(data.get("user", ""))
    assistant = str(data.get("assistant", ""))
    system = str(data.get("system", ""))
    hist = data.get("history") or []
    return len(user) + len(assistant) + len(system) + sum(
        len(str(t.get("content", ""))) for t in hist if isinstance(t, dict)
    )


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    line_no: int
    level: str       # "error" | "warning"
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"line_no": self.line_no, "level": self.level,
                "message": self.message}


@dataclass
class ValidationReport:
    ok: bool
    path: str
    sample_count: int = 0
    valid_count: int = 0
    size_bytes: int = 0
    issues: list = field(default_factory=list)
    preview: list = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "path": self.path,
            "sample_count": self.sample_count,
            "valid_count": self.valid_count,
            "size_bytes": self.size_bytes,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues[:MAX_ISSUES]],
            "preview": list(self.preview),
        }


def _validate_one_line(data: Any) -> str | None:
    """返回错误信息，None = 通过。"""
    if not isinstance(data, dict):
        return "not a JSON object"
    user = data.get("user")
    assistant = data.get("assistant")
    if not isinstance(user, str) or not user.strip():
        return "'user' must be non-empty string"
    if not isinstance(assistant, str) or not assistant.strip():
        return "'assistant' must be non-empty string"
    history = data.get("history")
    if history is not None and not isinstance(history, list):
        return "'history' must be list if present"
    system = data.get("system")
    if system is not None and not isinstance(system, str):
        return "'system' must be string if present"
    return None


def validate_jsonl(
    path: str,
    *,
    max_lines: int = 0,
) -> ValidationReport:
    """读文件做校验。max_lines=0 表示全部扫描。"""
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path required")
    p = Path(path)
    report = ValidationReport(ok=False, path=str(p))

    if not p.exists():
        report.issues.append(ValidationIssue(0, "error", "file not found"))
        return report
    if not p.is_file():
        report.issues.append(ValidationIssue(0, "error", "not a regular file"))
        return report

    try:
        report.size_bytes = int(p.stat().st_size)
    except OSError as exc:
        report.issues.append(ValidationIssue(0, "error", f"stat failed: {exc}"))
        return report

    sample_count = 0
    valid_count = 0
    preview = []
    with p.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            if max_lines and line_no > max_lines:
                break
            text = raw.strip()
            if not text or text.startswith("#"):
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                report.issues.append(ValidationIssue(
                    line_no, "error", f"invalid JSON: {exc.msg}",
                ))
                continue
            err = _validate_one_line(data)
            if err:
                report.issues.append(ValidationIssue(line_no, "error", err))
                continue
            sample_count += 1

            # 长度过滤（与 preprocessor.filter_by_length 一致）
            n = _sample_char_count(data)
            if n < MIN_SAMPLE_CHARS:
                report.issues.append(ValidationIssue(
                    line_no, "warning",
                    f"样本仅 {n} 字符（< {MIN_SAMPLE_CHARS}），训练时会被过滤",
                ))
                continue
            if n > MAX_SAMPLE_CHARS:
                report.issues.append(ValidationIssue(
                    line_no, "warning",
                    f"样本 {n} 字符（> {MAX_SAMPLE_CHARS}），训练时会被过滤",
                ))
                continue

            valid_count += 1
            if len(preview) < MAX_PREVIEW_LINES:
                preview.append({
                    "line_no": line_no,
                    "user": str(data.get("user", ""))[:120],
                    "assistant": str(data.get("assistant", ""))[:120],
                    "has_system": bool(data.get("system")),
                    "history_turns": len(data.get("history") or []),
                })

    report.sample_count = sample_count
    report.valid_count = valid_count
    report.preview = preview
    report.ok = report.error_count == 0 and valid_count > 0
    if valid_count == 0 and report.error_count == 0:
        if sample_count == 0:
            report.issues.append(ValidationIssue(0, "error",
                "no valid samples found"))
        else:
            report.issues.append(ValidationIssue(0, "error",
                f"所有 {sample_count} 条样本都短于 {MIN_SAMPLE_CHARS} 字符，"
                f"训练时会全部被过滤 → dataset empty"))
    return report


def validate_dataset_spec(spec: Any) -> list[str]:
    """快速检查 DatasetSpec 是否自洽。返回错误列表。"""
    errs: list[str] = []
    if not hasattr(spec, "path"):
        return ["spec missing .path"]
    p = Path(str(getattr(spec, "path", "")))
    if not p.exists():
        errs.append(f"path not exist: {p}")
    if hasattr(spec, "size_bytes") and getattr(spec, "size_bytes") < 0:
        errs.append("size_bytes < 0")
    return errs


__all__ = [
    "ValidationIssue", "ValidationReport",
    "validate_jsonl", "validate_dataset_spec",
    "MAX_PREVIEW_LINES", "MAX_ISSUES",
]
