"""Part 1 of pipeline.py."""
from __future__ import annotations

from backend.workspace.path_normalizer import normalize_workspace_path

from typing import Any, Dict, Optional

from backend.platform.approval_gate import ApprovalGate

from backend.platform.event_bridge import EventBridge

from backend.platform.memory_bridge import MemoryBridge

from backend.platform.pipeline_phases import PipelinePhasesMixin

from backend.platform.proposal import Proposal

from backend.platform.request import CodingRequest

from backend.platform.session import CodingSession

from ..pipeline_io import emit_event, read_primary

__all__ = ["PlatformPipeline"]
