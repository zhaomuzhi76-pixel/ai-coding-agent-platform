"""BuiltinIgnores: 工业级内置忽略规则。

契约：
  - 目录名黑名单（任何层级命中即忽略）
  - 文件名黑名单（同上）
  - 后缀黑名单（编译产物）
  - 大小阈值（单文件超过则忽略）

不负责：
  - .gitignore 解析（gitignore_parser 管）
  - 磁盘扫描 / 缓存 / 分页
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


DEFAULT_DIR_BLACKLIST = (
    ".git", ".svn", ".hg",
    # 凭据目录（阿里云 / Codex / Claude Code 均视为始终禁止）
    ".ssh", ".aws", ".gnupg", ".kube", ".docker",
    "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "target",
    ".idea", ".vscode", ".vs",
    "coverage", ".coverage",
    "vendor", "bower_components",
    # AI / 模型资产（工业级默认忽略）
    ".huggingface", ".tts_cache", "checkpoints", "gfpgan",
    "installer_files", "site-packages", ".cache", "logs",
)

DEFAULT_FILE_BLACKLIST = (
    ".DS_Store", "Thumbs.db", "desktop.ini",
    # 环境变量
    ".env", ".env.local", ".env.production", ".env.development",
    # 密钥文件
    "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
    "authorized_keys", "known_hosts",
    # CLI 凭据
    ".netrc", ".npmrc", ".pypirc", ".git-credentials",
)

DEFAULT_SUFFIX_BLACKLIST = (
    ".pyc", ".pyo", ".pyd",
    ".o", ".a", ".so", ".dylib", ".dll", ".exe",
    ".class", ".jar",
    ".log", ".tmp", ".swp", ".swo",
    ".min.js.map", ".map",
    # AI 模型资产
    ".trt", ".pt", ".pth", ".ckpt", ".safetensors",
    ".onnx", ".tflite", ".bin", ".h5", ".pb",
)

DEFAULT_MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB


@dataclass(frozen=True, slots=True)
class IgnoreDecision:
    ignored: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ignored


class BuiltinIgnores:
    VERSION = "1.0"

    def __init__(
        self,
        dir_blacklist: Iterable[str] | None = None,
        file_blacklist: Iterable[str] | None = None,
        suffix_blacklist: Iterable[str] | None = None,
        max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    ) -> None:
        self.dir_blacklist = frozenset(dir_blacklist or DEFAULT_DIR_BLACKLIST)
        self.file_blacklist = frozenset(file_blacklist or DEFAULT_FILE_BLACKLIST)
        self.suffix_blacklist = tuple(suffix_blacklist or DEFAULT_SUFFIX_BLACKLIST)
        self.max_file_bytes = int(max_file_bytes)

    def decide(
        self,
        name: str,
        *,
        is_dir: bool,
        size: int = 0,
    ) -> IgnoreDecision:
        if not isinstance(name, str) or not name:
            return IgnoreDecision(True, "empty-name")

        if is_dir:
            if name in self.dir_blacklist:
                return IgnoreDecision(True, "dir-blacklist:" + name)
            return IgnoreDecision(False)

        if name in self.file_blacklist:
            return IgnoreDecision(True, "file-blacklist:" + name)

        for suffix in self.suffix_blacklist:
            if name.endswith(suffix):
                return IgnoreDecision(True, "suffix:" + suffix)

        if size > self.max_file_bytes:
            return IgnoreDecision(True, "too-large:" + str(size))

        return IgnoreDecision(False)

    def ready(self) -> bool:
        return bool(self.dir_blacklist) and self.max_file_bytes > 0

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "dir_blacklist_size": len(self.dir_blacklist),
            "file_blacklist_size": len(self.file_blacklist),
            "suffix_blacklist_size": len(self.suffix_blacklist),
            "max_file_bytes": self.max_file_bytes,
            "ready": self.ready(),
        }


__all__ = [
    "BuiltinIgnores",
    "IgnoreDecision",
    "DEFAULT_DIR_BLACKLIST",
    "DEFAULT_FILE_BLACKLIST",
    "DEFAULT_SUFFIX_BLACKLIST",
    "DEFAULT_MAX_FILE_BYTES",
]
