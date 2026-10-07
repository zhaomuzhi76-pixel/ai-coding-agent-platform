"""WorkspacePath：工作区路径的权威解析边界。

工业级契约（参考 Codex PathMapper / Qwen WorkspaceFileSystem）：
  1. 所有入站路径必须经过 resolve()
  2. 嵌入式 WSL UNC 从任意位置抠出并归一化
  3. 逃逸出工作区的路径被拒绝（fail-loud，绝不静默降级）
  4. 返回 branded WorkspacePath，类型系统保证下游安全
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


class WorkspacePathError(RuntimeError):
    """路径无法被安全解析时抛出。永不静默降级。"""


class PathOutsideWorkspace(WorkspacePathError):
    """解析后的路径逃逸出工作区边界。"""


class UnsupportedPathForm(WorkspacePathError):
    """路径形式无法被识别。"""


# 嵌入式 WSL UNC —— 出现在字符串任意位置，不锚定开头。
# 前缀可能是 CWD 拼上的任意内容。
_UNC_WSL = re.compile(
    r'\\{2,}wsl(?:\.localhost|\$)[\\/]+([^\\/]+)[\\/]+([\s\S]+)$',
    re.IGNORECASE,
)
# \\?\C:\Users\...  → /mnt/c/Users/...
_UNC_DRIVE_LONG = re.compile(
    r'^\\\\\?\\([A-Za-z]):[\\/](.+)$',
)


@dataclass(frozen=True, slots=True)
class WorkspacePath:
    """经过权威解析的工作区路径。构造即安全。"""
    value: str

    def __str__(self) -> str:
        return self.value

    def __fspath__(self) -> str:
        return self.value


def resolve(workspace_root: str, path: str) -> WorkspacePath:
    """权威解析入口。所有文件操作必须调用此函数。

    步骤：
      1. 归一化 workspace_root（含嵌入式 UNC 抠除）
      2. 从 path 中抠出嵌入式 UNC（若有）
      3. 相对路径拼到 root 上
      4. realpath 后校验是否仍在工作区内
    """
    root = _canonicalize(workspace_root)
    if not root:
        raise UnsupportedPathForm("empty workspace root")

    extracted = _extract_wsl_unc(path)
    raw = extracted if extracted is not None else (path or "").strip()
    if not raw:
        raise UnsupportedPathForm("empty path")

    p = _canonicalize(raw)
    abs_path = p if os.path.isabs(p) else os.path.join(root, p)

    try:
        resolved = str(Path(abs_path).resolve())
    except (OSError, RuntimeError) as exc:
        raise WorkspacePathError(
            f"cannot resolve {abs_path!r}: {exc}"
        ) from exc

    if not _is_under(resolved, root):
        raise PathOutsideWorkspace(
            f"path escapes workspace: {resolved!r} not under {root!r}"
        )
    return WorkspacePath(resolved)


def _extract_wsl_unc(path: str) -> str | None:
    """若 path 含嵌入式 WSL UNC，返回 Linux 绝对路径；否则 None。"""
    if not isinstance(path, str) or not path:
        return None
    m = _UNC_WSL.search(path)
    if not m:
        return None
    rest = m.group(2).replace("\\", "/")
    return "/" + rest.lstrip("/")


def _canonicalize(p: str) -> str:
    r"""只做归一化，不做路径拼接。

    支持 4 种输入形态：
      1. 嵌入式 WSL UNC —— \\wsl.localhost\<distro>\... 或 \\wsl$\...
      2. Windows 长 UNC —— \\?\C:\Users\...
      3. Windows 盘符   —— C:\Users\... 或 C:/Users/...
      4. 其它 UNC       —— \\server\share\...
    普通 POSIX 路径原样返回。
    """
    if not isinstance(p, str):
        return ""
    s = p.strip()
    if not s:
        return ""

    # 1. 嵌入式 WSL UNC（任意位置，含 CWD 前缀污染）
    extracted = _extract_wsl_unc(s)
    if extracted is not None:
        return extracted

    # 2. \\?\C:\...
    m = _UNC_DRIVE_LONG.match(s)
    if m:
        drive = m.group(1).lower()
        rest = m.group(2).replace("\\", "/")
        return f"/mnt/{drive}/{rest}"

    # 3. C:\... 或 C:/...
    if len(s) >= 3 and s[1] == ":" and s[2] in ("\\", "/"):
        drive = s[0].lower()
        rest = s[3:].replace("\\", "/")
        return f"/mnt/{drive}/{rest}"

    # 4. 其它 UNC：\\server\share\...
    if s.startswith("\\\\"):
        rest = s.lstrip("\\").replace("\\", "/")
        return "//" + rest

    return s


def _is_under(path: str, root: str) -> bool:
    """path 是否在 root 之下（含 root 本身）。"""
    if path == root:
        return True
    prefix = root if root.endswith(os.sep) else root + os.sep
    return path.startswith(prefix)


def normalize_only(path: str) -> str:
    r"""只做归一化，不做边界检查。

    用于入口处一次性清洗 payload，返回干净的 POSIX 路径：
      - 嵌入式 WSL UNC  → 抠出 Linux 路径
      - C:\x 盘符路径   → /mnt/c/x
      - 普通路径         → 原样返回
    """
    if not isinstance(path, str):
        return ""
    p = path.strip()
    if not p:
        return ""
    return _canonicalize(p)


__all__ = [
    "WorkspacePath",
    "WorkspacePathError",
    "PathOutsideWorkspace",
    "UnsupportedPathForm",
    "resolve",
    "normalize_only",
]
