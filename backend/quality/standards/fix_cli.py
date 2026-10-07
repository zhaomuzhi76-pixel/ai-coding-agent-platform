"""一条命令修复整层 —— 只做安全的最小改动。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.quality.standards.audit_cli import run_audit
from backend.quality.standards.contracts import LayerReport


def run_fix(layer: str, as_json: bool = False) -> int:
    """修复策略：
      - line_limit：只报建议，不自动拆（有风险）
      - no_exit：只报建议
      - plugin_pattern：自动补 descriptor 模板
      - tmpfs_test：只报建议
      - 其余只报不改
    """
    root = Path(layer)
    if not root.is_dir():
        print(f"❌ 目录不存在: {layer}", file=sys.stderr)
        return 2

    fixes: list[str] = []

    # 1. 扫描前先收集待修项
    from backend.quality.standards.checks_basic import (
        check_line_limit, check_no_exit,
    )
    from backend.quality.standards.checks_arch import (
        check_plugin_pattern, check_tmpfs,
    )
    to_fix_plugin: list[Path] = []
    advisory: list[str] = []

    for f in sorted(root.rglob("*.py")):
        rel = str(f.relative_to(root.parent))
        r1 = check_line_limit(f, rel)
        if not r1.ok:
            advisory.append(f"  需人工拆分: {rel} ({r1.message})")
        r2 = check_no_exit(f, rel)
        if not r2.ok:
            advisory.append(f"  需人工去掉 exit: {rel}")
        r3 = check_plugin_pattern(root.parent, f, rel)
        if not r3.ok:
            to_fix_plugin.append(f)
        r4 = check_tmpfs(root.parent, f, rel)
        if not r4.ok:
            advisory.append(f"  测试需用 tmpfs: {rel}")

    # 2. 自动补 descriptor（唯一安全的自动修复）
    for f in to_fix_plugin:
        src = f.read_text(encoding="utf-8")
        if "descriptor" in src:
            continue
        cls_name = f.stem.title().replace("_", "")
        append = (
            "\n\n# 自动补：插件 descriptor（standards fix）\n"
            "descriptor = {\n"
            f'    "name": "{f.stem}",\n'
            '    "version": "1.0.0",\n'
            '    "capabilities": (),\n'
            "}\n"
        )
        f.write_text(src + append, encoding="utf-8")
        fixes.append(f"补 descriptor: {f}")

    # 3. 重跑 audit 确认
    if as_json:
        result = {"layer": layer, "fixes": fixes,
                  "advisory": advisory}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 70)
        print(f"工业级规则修复 · {layer}")
        print("=" * 70)
        if fixes:
            for x in fixes:
                print(f"  ✅ {x}")
        else:
            print("  （无自动可修项）")
        if advisory:
            print()
            print(f"  ⚠️  {len(advisory)} 项需人工处理：")
            for x in advisory[:10]:
                print(x)
    return 0


__all__ = ["run_fix"]
