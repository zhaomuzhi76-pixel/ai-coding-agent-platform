from __future__ import annotations

from typing import Any

from backend.agent.planner.builders.analysis_builder import AnalysisBuilder
from backend.agent.planner.builders.code_modify_builder import CodeModifyBuilder
from backend.agent.planner.builders.deployment_builder import DeploymentBuilder
from backend.agent.planner.builders.file_edit_builder import FileEditBuilder
from backend.agent.planner.builders.file_read_builder import FileReadBuilder
from backend.agent.planner.builders.fix_error_builder import FixErrorBuilder
from backend.agent.planner.builders.multi_file_edit_builder import (
    MultiFileEditBuilder,
)
from backend.agent.planner.builders.project_analysis_builder import (
    ProjectAnalysisBuilder,
)
from backend.agent.planner.builders.summary_builder import SummaryBuilder
from backend.agent.planner.builders.testing_builder import TestingBuilder
from backend.agent.planner.builders.text_generate_builder import (
    TextGenerateBuilder,
)
from backend.agent.planner.builders.workspace_builder import WorkspaceBuilder


def register_defaults(registry: Any) -> None:
    """注册全部默认 builder。"""
    registry.register("file_edit", FileEditBuilder())
    registry.register("file_read", FileReadBuilder())
    registry.register("workspace_scan", WorkspaceBuilder())
    registry.register("deployment", DeploymentBuilder())
    registry.register("test", TestingBuilder())
    registry.register("summary", SummaryBuilder())
    registry.register("text_generate", TextGenerateBuilder())
    registry.register("code_analysis", AnalysisBuilder())
    registry.register("code_modify", CodeModifyBuilder())
    registry.register("edit_multiple_files", MultiFileEditBuilder())
    registry.register("understand_project", ProjectAnalysisBuilder())
    registry.register("fix_error", FixErrorBuilder())


__all__ = ["register_defaults"]
