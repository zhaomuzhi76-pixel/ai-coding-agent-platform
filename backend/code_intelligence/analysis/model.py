from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class FunctionModel:
    name: str
    async_function: bool = False

@dataclass
class ClassModel:
    name: str
    methods: list[FunctionModel] = field(
        default_factory=list
    )

@dataclass
class ImportModel:
    module: str

@dataclass
class CodeFileModel:
    path: str
    language: str = "python"
    lines: int = 0
    classes: list[ClassModel] = field(
        default_factory=list
    )
    functions: list[FunctionModel] = field(
        default_factory=list
    )
    imports: list[ImportModel] = field(
        default_factory=list
    )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "path": self.path,
            "language": self.language,
            "lines": self.lines,
            "classes": [
                item.name
                for item in self.classes
            ],
            "functions": [
                item.name
                for item in self.functions
            ],
            "imports": [
                item.module
                for item in self.imports
            ],
        }

__all__ = [
    "FunctionModel",
    "ClassModel",
    "ImportModel",
    "CodeFileModel",
]
