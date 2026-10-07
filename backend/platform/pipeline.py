"""PlatformPipeline: 7-phase coding request orchestrator.

Phase 1-2: plan + propose   -> CodeEditOrchestrator
Phase 3:   approve / reject -> ApprovalGate
Phase 4-7: apply/verify/learn -> PipelinePhasesMixin (pipeline_phases.py)
\n\nCompat shim. See ._pipeline_parts."""
from __future__ import annotations
from ._pipeline_parts import *  # noqa
from ._pipeline_parts import (PlatformPipeline,)  # noqa
