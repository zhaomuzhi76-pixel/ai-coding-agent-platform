"""Excellence layer: Codex + Claude Code + Aliyun advantages combined.

职责边界：
    code_intelligence.*     -> 冻结：patch / workflow / verify / analyze
    platform.*              -> 编排：会话 + 提案 + 审批 + 桥接
    observability.*         -> tracer / alert / report / viz
    excellence.codex        -> Codex 优势
    excellence.claude       -> Claude 优势
    excellence.aliyun       -> 阿里云优势
    excellence.orchestrator -> 三家优势总装
"""
from backend.excellence.codex import (
    ContextChunk, SelectedContext, ContextSelector,
    BoundaryViolation, BoundaryReport, BoundaryChecker,
    DiffIssue, DiffReport, DiffVerifier,
    StepCommit, StepCommitPlan, StepCommitPlanner,
)
from backend.excellence.claude import (
    ModuleNode, RepoMap, RepoMapper,
    CallNode, CallChain, CallTracer,
    ADR, ADRLog,
    EvolutionSnapshot, TrendPoint, EvolutionTracker,
)
from backend.excellence.aliyun import (
    CompletionContext, Completion, CompletionEngine, prefix_completer,
    FunctionSpec, TestDraft, TestGenerator,
    DocstringDraft, DocstringWriter,
    RuleViolation, Rule, ReviewReport, RuleReviewer,
    DeployProfile, DeployProfileBuilder,
)
from backend.excellence.report import ExcellenceReport
from backend.excellence.orchestrator import ExcellenceOrchestrator

__all__ = [
    # codex
    "ContextChunk", "SelectedContext", "ContextSelector",
    "BoundaryViolation", "BoundaryReport", "BoundaryChecker",
    "DiffIssue", "DiffReport", "DiffVerifier",
    "StepCommit", "StepCommitPlan", "StepCommitPlanner",
    # claude
    "ModuleNode", "RepoMap", "RepoMapper",
    "CallNode", "CallChain", "CallTracer",
    "ADR", "ADRLog",
    "EvolutionSnapshot", "TrendPoint", "EvolutionTracker",
    # aliyun
    "CompletionContext", "Completion", "CompletionEngine", "prefix_completer",
    "FunctionSpec", "TestDraft", "TestGenerator",
    "DocstringDraft", "DocstringWriter",
    "RuleViolation", "Rule", "ReviewReport", "RuleReviewer",
    "DeployProfile", "DeployProfileBuilder",
    # orchestrator
    "ExcellenceReport", "ExcellenceOrchestrator",
]
