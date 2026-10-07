from __future__ import annotations

import os
import re


_WSL_HOST_RE = re.compile(
    r"^[\\\\/]+(wsl\.localhost|wsl\$)[\\\\/][^\\\\/]+[\\\\/](.*)$",
    re.IGNORECASE,
)
_WIN_DRIVE_RE = re.compile(
    r"^([A-Za-z]):[\\\\/](.*)$",
)


def normalize_workspace_path(value: str) -> str:
    """
    把跨平台路径归一化为当前 Linux/WSL 的绝对路径。

    支持输入：
      - Linux 绝对路径：/home/...
      - WSL UNC：      \\\\wsl.localhost\\Ubuntu-24.04\\home\\user\\proj
      - WSL UNC 旧式：  \\\\wsl$\\Ubuntu-24.04\\home\\user\\proj
      - Windows 盘符：  C:\\Users\\...  E:\\proj\\...
      - 已带 CWD 前缀： /some/cwd/\\\\wsl.localhost\\Distro\\...
    """
    if not isinstance(value, str) or not value.strip():
        return "."

    # 1. 去首尾空白
    s = value.strip()

    # 2. 如果内部含 WSL UNC 片段，先截出来（去掉前置的 cwd 前缀）
    marker = re.search(
        r"[\\\\/]+(wsl\.localhost|wsl\$)[\\\\/]",
        s,
        re.IGNORECASE,
    )
    if marker:
        s = s[marker.start():]

    # 3. WSL UNC → /path
    m = _WSL_HOST_RE.match(s)
    if m:
        tail = m.group(2).replace("\\", "/")
        return "/" + tail.lstrip("/")

    # 4. Windows 盘符 → /mnt/x/path
    m = _WIN_DRIVE_RE.match(s)
    if m:
        drive = m.group(1).lower()
        rest = m.group(2).replace("\\", "/")
        return "/mnt/" + drive + "/" + rest.lstrip("/")

    # 5. 反斜杠 → 正斜杠（Windows 用户可能传相对路径）
    s = s.replace("\\", "/")

    # 6. 绝对路径直接用
    if s.startswith("/"):
        return os.path.normpath(s)

    # 7. 相对路径 → 用 CWD 拼（尽力）
    return os.path.normpath(s)


__all__ = ["normalize_workspace_path"]
