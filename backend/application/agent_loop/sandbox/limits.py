"""沙箱资源限制。"""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SandboxLimits:
    cpu_seconds: int = 60
    memory_mb: int = 512
    file_size_mb: int = 10
    open_files: int = 64


__all__ = ["SandboxLimits"]
