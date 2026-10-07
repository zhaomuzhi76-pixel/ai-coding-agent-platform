"""benchmark 报告下载（JSON / CSV）"""
import csv
import io
import json
from typing import Any, Dict


def to_json(run: Dict[str, Any]) -> str:
    return json.dumps(run, ensure_ascii=False, indent=2)


def to_csv(run: Dict[str, Any]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["run_id", "provider", "model", "score", "passed",
                "case_id", "name", "category", "case_passed",
                "case_score", "latency_ms", "cost", "note"])
    for c in run.get("cases", []):
        w.writerow([
            run.get("run_id", ""), run.get("provider", ""),
            run.get("model", ""), run.get("score", 0),
            run.get("passed_count", 0),
            c.get("case_id", ""), c.get("name", ""),
            c.get("category", ""), c.get("passed", False),
            c.get("score", 0), c.get("latency_ms", 0),
            c.get("cost", 0), c.get("note", ""),
        ])
    return buf.getvalue()


def to_markdown(run: Dict[str, Any]) -> str:
    lines = [
        f"# Benchmark Report · {run.get('model', '?')}",
        "",
        f"- Provider: `{run.get('provider', '')}`",
        f"- Run ID: `{run.get('run_id', '')}`",
        f"- Score: **{float(run.get('score', 0)):.1f}**",
        f"- Passed: {run.get('passed_count', 0)}/{run.get('case_count', 0)}",
        "",
        "## 用例明细",
        "",
        "| 用例 | 类别 | 通过 | 分数 | 延迟 | 备注 |",
        "|---|---|---|---|---|---|",
    ]
    for c in run.get("cases", []):
        lines.append(
            f"| {c.get('name', '')} | {c.get('category', '')} | "
            f"{'✅' if c.get('passed') else '❌'} | "
            f"{float(c.get('score', 0)) * 100:.0f} | "
            f"{float(c.get('latency_ms', 0)):.0f}ms | {c.get('note', '')} |"
        )
    return "\n".join(lines)
