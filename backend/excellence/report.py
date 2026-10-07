"""ExcellenceReport: unified result of the excellence pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ExcellenceReport:
    """Aggregated result of a full excellence run."""

    repo: Dict[str, Any] = field(default_factory=dict)
    call_chains: List[Dict[str, Any]] = field(default_factory=list)
    selected_context: Dict[str, Any] = field(default_factory=dict)
    boundary: Dict[str, Any] = field(default_factory=dict)
    completions: List[Dict[str, Any]] = field(default_factory=list)
    test_draft: Dict[str, Any] = field(default_factory=dict)
    docstring_drafts: List[Dict[str, Any]] = field(default_factory=list)
    diff: Dict[str, Any] = field(default_factory=dict)
    rule_review: Dict[str, Any] = field(default_factory=dict)
    step_commit: Dict[str, Any] = field(default_factory=dict)
    adr: List[Dict[str, Any]] = field(default_factory=list)
    evolution: Dict[str, Any] = field(default_factory=dict)
    deploy: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def stages_present(self) -> List[str]:
        out: List[str] = []
        if self.repo: out.append("repo")
        if self.call_chains: out.append("call_chains")
        if self.selected_context: out.append("context")
        if self.boundary: out.append("boundary")
        if self.completions: out.append("completion")
        if self.test_draft: out.append("test")
        if self.docstring_drafts: out.append("docstring")
        if self.diff: out.append("diff")
        if self.rule_review: out.append("rule_review")
        if self.step_commit: out.append("step_commit")
        if self.adr: out.append("adr")
        if self.evolution: out.append("evolution")
        if self.deploy: out.append("deploy")
        return out

    @property
    def ok(self) -> bool:
        if self.errors:
            return False
        if self.diff and not self.diff.get("ok", True):
            return False
        if self.rule_review and not self.rule_review.get("ok", True):
            return False
        return True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "stages": self.stages_present(),
            "repo": self.repo,
            "call_chains": self.call_chains,
            "selected_context": self.selected_context,
            "boundary": self.boundary,
            "completions": self.completions,
            "test_draft": self.test_draft,
            "docstring_drafts": self.docstring_drafts,
            "diff": self.diff,
            "rule_review": self.rule_review,
            "step_commit": self.step_commit,
            "adr": self.adr,
            "evolution": self.evolution,
            "deploy": self.deploy,
            "errors": list(self.errors),
        }

    def as_text(self) -> str:
        lines = ["=== Excellence Report ==="]
        lines.append(f"OK: {self.ok}")
        lines.append(f"Stages: {', '.join(self.stages_present()) or '(none)'}")
        if self.repo:
            lines.append(
                f"Repo: {self.repo.get('files', 0)} files, "
                f"{self.repo.get('total_lines', 0)} lines, "
                f"{self.repo.get('packages', 0)} packages"
            )
        if self.call_chains:
            lines.append(f"Call chains: {len(self.call_chains)}")
        if self.selected_context:
            sc = self.selected_context
            lines.append(
                f"Context: {sc.get('used_chars', 0)}/"
                f"{sc.get('budget_chars', 0)} chars, "
                f"coverage={sc.get('coverage', 0)}"
            )
        if self.boundary:
            lines.append(
                f"Boundary: ok={self.boundary.get('ok')} "
                f"checked={self.boundary.get('checked_imports', 0)}"
            )
        if self.rule_review:
            rr = self.rule_review
            lines.append(
                f"Rule review: ok={rr.get('ok')} "
                f"violations={rr.get('total', 0)} "
                f"by_dim={rr.get('by_dimension', {})}"
            )
        if self.step_commit:
            lines.append(
                f"Step commit: {self.step_commit.get('step_count', 0)} steps, "
                f"{self.step_commit.get('file_count', 0)} files"
            )
        if self.deploy:
            lines.append(f"Deploy: {self.deploy.get('service')}")
        if self.errors:
            lines.append("Errors:")
            for e in self.errors:
                lines.append(f"  - {e}")
        return "\n".join(lines)

    def dump(self) -> Dict[str, Any]:
        return self.as_dict()


__all__ = ["ExcellenceReport"]
