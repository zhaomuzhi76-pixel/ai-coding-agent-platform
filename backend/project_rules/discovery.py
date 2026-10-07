"""动态探测项目结构 —— 零硬编码。

职责：
  - detect_extensions：项目实际用到的代码后缀
  - detect_scan_roots：含代码的直接子目录
  - detect_layers：按命名约定（L0_/layer1_）探测层
不重复职责：只读不写，不缓存，无候选列表。
"""
from __future__ import annotations

import re
from pathlib import Path


# 只过滤"绝对不会放业务代码"的目录（非业务候选）
# 物理隔离目录（含依赖/缓存/构建产物）—— 唯一真相源
# 任何 checker 都应通过 discovery.should_skip 使用，不得自行定义
_SKIP_DIRS = frozenset({
    # 依赖
    "node_modules", "site-packages", "dist-packages",
    "bower_components", "vendor",
    # Python 缓存
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".pytype", ".hypothesis",
    ".tox", ".nox", ".eggs",
    # 构建产物
    "dist", "build", "out", "target", "bin", "obj",
    ".gradle", ".mvn",
    # 版本控制
    ".git", ".svn", ".hg",
    # 虚拟环境
    ".venv", "venv", "env", ".env", ".conda",
    # IDE
    ".idea", ".vscode", ".vs", ".fleet",
    # 测试覆盖
    "htmlcov", "coverage", ".coverage",
    # JS 生态缓存
    ".cache", ".parcel-cache", ".next", ".nuxt",
    ".turbo", ".vite", ".svelte-kit", ".angular",
    # 系统
    ".Trash", "$RECYCLE.BIN",
})

# 代码后缀从"实际扫描结果"推导，这里仅作为 fallback 兜底
_FALLBACK_EXTS = (".py",)

# 层命名约定（正则，非候选列表）
_LAYER_RE = re.compile(r"^(?:[Ll]|[Ll]ayer)[_-]?(\d+)", re.IGNORECASE)


def _should_skip(p: Path) -> bool:
    return any(part in _SKIP_DIRS for part in p.parts)


def should_skip(p: Path) -> bool:
    """公开：判断路径是否应跳过（任何 checker 复用此逻辑）。"""
    return any(part in _SKIP_DIRS for part in p.parts)


def _iter_files(root: Path):
    """遍历 root 下所有非跳过目录的文件。"""
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if _should_skip(p):
            continue
        yield p


def detect_extensions(root: Path) -> list[str]:
    """扫描项目，收集所有代码后缀（无候选列表）。"""
    seen: set[str] = set()
    for f in _iter_files(root):
        ext = f.suffix.lower()
        if not ext or len(ext) > 5:
            continue
        # 只保留"常见代码后缀"（.py/.ts/.tsx/.js/.go/.rs/...）
        # 通过内容判断：后缀前无点，且不含数字/特殊符号
        if ext[1:].isalpha():
            seen.add(ext)
    # 排除已知非代码后缀
    _NON_CODE = frozenset({
        ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
        ".cfg", ".ini", ".log", ".lock", ".csv", ".svg",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp",
        ".html", ".css", ".scss", ".less", ".xml",
    })
    code_exts = sorted(seen - _NON_CODE)
    return code_exts or list(_FALLBACK_EXTS)


def detect_scan_roots(root: Path) -> list[str]:
    """扫描 root 直接子目录，返回含代码的目录名。"""
    out: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in _SKIP_DIRS or child.name.startswith("."):
            continue
        # 该子目录里是否有至少一个代码文件
        if next(iter(_iter_files(child)), None) is not None:
            out.append(child.name)
    return out or ["."]


def detect_layers(root: Path) -> dict[str, list[str]]:
    """按命名约定 L0_/L1_/layer0/layer_1 探测层。

    无匹配时返回 {}（checker 会退化为"不做层检查"）。
    """
    layers: dict[str, list[str]] = {}
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        m = _LAYER_RE.match(child.name)
        if not m:
            continue
        key = f"L{int(m.group(1))}"
        layers.setdefault(key, []).append(
            child.relative_to(root).as_posix()
        )
    return layers


__all__ = [
    "detect_extensions", "detect_scan_roots", "detect_layers",
    "should_skip",
]
