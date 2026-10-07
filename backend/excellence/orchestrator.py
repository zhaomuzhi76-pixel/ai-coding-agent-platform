"""ExcellenceOrchestrator: three-vendor capability pipeline.

阶段：
    1. understand    (Claude)  repo map + call chains
    2. plan          (Codex)   context selection + boundary check
    3. generate      (Aliyun)  completions + tests + docstrings
    4. verify        (Codex + Aliyun) diff verify + rule review
    5. commit        (Codex)   step commit plan
    6. record        (Claude)  ADR + evolution snapshot
    7. deploy        (Aliyun)  docker / k8s profile

所有能力从 excellence.{codex,claude,aliyun} 复用，本类只编排。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from backend.excellence.aliyun.completion import (
    Completion, CompletionContext, CompletionEngine,
)
from backend.excellence.aliyun.deploy_profile import (
    DeployProfile, DeployProfileBuilder,
)
from backend.excellence.aliyun.docstring_writer import DocstringWriter
from backend.excellence.aliyun.rule_review import RuleReviewer
from backend.excellence.aliyun.test_generator import TestGenerator
from backend.excellence.claude.adr import ADRLog
from backend.excellence.claude.call_tracer import CallTracer
from backend.excellence.claude.evolution_tracker import EvolutionTracker
from backend.excellence.claude.repo_map import RepoMap, RepoMapper
from backend.excellence.codex.boundary_checker import BoundaryChecker
from backend.excellence.codex.context_selector import (
    ContextChunk, ContextSelector,
)
from backend.excellence.codex.diff_verifier import DiffVerifier
from backend.excellence.codex.step_commit import StepCommitPlanner
from backend.excellence.report import ExcellenceReport


class ExcellenceOrchestrator:
    VERSION = "1.0"

    def __init__(self, max_step_files: int = 3) -> None:
        self._repo = RepoMapper()
        self._tracer = CallTracer()
        self._ctx = ContextSelector()
        self._boundary = BoundaryChecker()
        self._diff = DiffVerifier()
        self._rules = RuleReviewer()
        self._steps = StepCommitPlanner(max_files_per_step=max_step_files)
        self._adr = ADRLog()
        self._evo = EvolutionTracker()
        self._docstring = DocstringWriter()
        self._tests = TestGenerator()
        self._deploy = DeployProfileBuilder()

    # ─── Stage 1: understand ────────────────────────────────
    def understand(
        self, root: str,
        *, trace_target: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        repo_map = self._repo.build(root)
        self._tracer.index(root)
        chains: List = []
        if trace_target is not None:
            mod, name = trace_target
            chains = self._tracer.trace_to(mod, name)
        self._evo.capture(repo_map, label="understand")
        return {"repo_map": repo_map, "chains": chains}

    # ─── Stage 2: plan ──────────────────────────────────────
    def plan_context(
        self,
        chunks: Sequence[ContextChunk],
        *,
        budget_chars: int = 32000,
    ) -> Dict[str, Any]:
        selector = ContextSelector(budget_chars=budget_chars)
        return selector.select(chunks).dump()

    def check_boundary(
        self, source_path: str, source_text: str,
        *, module_name: str = "",
    ) -> Dict[str, Any]:
        return self._boundary.check_source(
            source_path, source_text, module_name=module_name,
        ).dump()

    # ─── Stage 3: generate ──────────────────────────────────
    def generate_completions(
        self,
        engine: CompletionEngine,
        context: CompletionContext,
    ) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in engine.complete(context)]

    def generate_test(
        self, module_path: str, source: str,
    ) -> Dict[str, Any]:
        return self._tests.generate(module_path, source).to_dict()

    def generate_docstrings(
        self, source: str,
    ) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._docstring.generate(source)]

    # ─── Stage 4: verify ────────────────────────────────────
    def verify_diff(
        self, file: str, before: str, after: str,
    ) -> Dict[str, Any]:
        return self._diff.verify(file, before, after).dump()

    def review_rules(
        self, file: str, source: str,
    ) -> Dict[str, Any]:
        return self._rules.review(file, source).dump()

    # ─── Stage 5: commit ────────────────────────────────────
    def plan_commits(
        self, changes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self._steps.plan(changes).dump()

    # ─── Stage 6: record ────────────────────────────────────
    def record_adr(
        self, title: str, context: str, decision: str,
        consequences: str = "", **extra: Any,
    ) -> str:
        adr = self._adr.propose(
            title=title, context=context, decision=decision,
            consequences=consequences, **extra,
        )
        return adr.adr_id

    def accept_adr(self, adr_id: str) -> None:
        self._adr.accept(adr_id)

    def adr_log(self) -> Dict[str, Any]:
        return self._adr.dump()

    def evolution(self) -> Dict[str, Any]:
        return self._evo.summary()

    # ─── Stage 7: deploy ────────────────────────────────────
    def deploy_profile(
        self, service: str = "backend",
    ) -> DeployProfile:
        return self._deploy.build_default(service)

    # ─── full run ───────────────────────────────────────────
    def run(
        self,
        root: str,
        *,
        source_file: str = "",
        source_text: str = "",
        before: str = "",
        after: str = "",
        changes: Optional[List[Dict[str, Any]]] = None,
    ) -> ExcellenceReport:
        report = ExcellenceReport()
        try:
            info = self.understand(root)
            report.repo = info["repo_map"].dump()
            report.call_chains = [c.to_dict() for c in info["chains"]]
            report.evolution = self._evo.summary()
        except Exception as exc:
            report.errors.append(f"understand: {exc}")
        if source_file and source_text:
            try:
                report.boundary = self.check_boundary(
                    source_file, source_text,
                )
                report.rule_review = self.review_rules(
                    source_file, source_text,
                )
                report.docstring_drafts = self.generate_docstrings(
                    source_text,
                )
                report.test_draft = self.generate_test(
                    source_file, source_text,
                )
            except Exception as exc:
                report.errors.append(f"analyze: {exc}")
        if before or after:
            try:
                report.diff = self.verify_diff(
                    source_file, before, after,
                )
            except Exception as exc:
                report.errors.append(f"diff: {exc}")
        if changes:
            try:
                report.step_commit = self.plan_commits(changes)
            except Exception as exc:
                report.errors.append(f"steps: {exc}")
        return report

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "adr": self._adr.dump(),
            "evolution": self._evo.dump(),
        }


__all__ = ["ExcellenceOrchestrator"]
