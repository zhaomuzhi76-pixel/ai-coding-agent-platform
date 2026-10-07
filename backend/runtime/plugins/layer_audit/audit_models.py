"""Layer Audit 数据结构。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class Unit:
    kind: str        # class | function | async_function | assign
    name: str
    lines: int
    methods: List[str] = field(default_factory=list)
    method_lines: List[int] = field(default_factory=list)


@dataclass
class FileProfile:
    path: str
    rel_path: str
    lines: int
    imports: List[str] = field(default_factory=list)
    internal_imports: List[str] = field(default_factory=list)
    units: List[Unit] = field(default_factory=list)


@dataclass
class DuplicateHit:
    name: str
    kind: str
    files: List[str] = field(default_factory=list)


@dataclass
class AuditReport:
    root: str
    files: List[FileProfile] = field(default_factory=list)
    duplicate_classes: List[DuplicateHit] = field(default_factory=list)
    duplicate_functions: List[DuplicateHit] = field(default_factory=list)
    internal_import_edges: List[tuple] = field(default_factory=list)
    oversized: List[FileProfile] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return sum(f.lines for f in self.files)
