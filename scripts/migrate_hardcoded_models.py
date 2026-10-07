"""一次性迁移脚本：把硬编码模型名替换为注册中心调用（自动 .bak 备份）

重要：跳过 model_registry/ 自身；legacy import 必须插在 from __future__ 之后。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SKIP_DIRS = {
    "tests", "__pycache__", ".git", "node_modules",
    "venv", ".venv", "dist", "build", "model_registry",
}
REPLACEMENTS = [
    ('"qwen2.5-coder:7b"', '_default_role_model("code")'),
    ('"ollama-local"', '_default_provider_id()'),
]
IMPORT_LINE = (
    "from backend.core.model_registry.legacy_compat import "
    "_default_role_model, _default_provider_id\n"
)
DQ = chr(34) * 3
SQ = chr(39) * 3


def _inject_import(text: str) -> str:
    if "legacy_compat" in text:
        return text
    lines = text.splitlines(keepends=True)
    idx = 0
    in_doc = False
    for i, line in enumerate(lines):
        s = line.strip()
        if i == 0 and s.startswith("#!"):
            idx = 1
            continue
        if not in_doc and (s.startswith(DQ) or s.startswith(SQ)):
            q = DQ if s.startswith(DQ) else SQ
            if s.count(q) >= 2:
                idx = i + 1
                continue
            in_doc = True
            idx = i + 1
            continue
        if in_doc:
            idx = i + 1
            if DQ in s or SQ in s:
                in_doc = False
            continue
        if s and not s.startswith("#"):
            idx = i
            break
    future_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("from __future__ import"):
            future_idx = i
            break
    if future_idx >= 0 and future_idx >= idx:
        idx = future_idx + 1
    lines.insert(idx, IMPORT_LINE)
    return "".join(lines)


def _process(p: Path) -> bool:
    text = p.read_text(encoding="utf-8")
    if not any(old in text for old, _ in REPLACEMENTS):
        return False
    original = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    text = _inject_import(text)
    p.with_suffix(p.suffix + ".bak").write_text(original, encoding="utf-8")
    p.write_text(text, encoding="utf-8")
    return True


def main(apply: bool) -> int:
    n = 0
    for p in BACKEND.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if any(old in text for old, _ in REPLACEMENTS):
            tag = "[APPLIED]" if apply else "[DRY]"
            print(f"{tag} {p.relative_to(ROOT)}")
            if apply:
                _process(p)
            n += 1
    print(f"Total: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
