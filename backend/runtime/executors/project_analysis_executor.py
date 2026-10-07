from __future__ import annotations
from backend.core.model_registry.legacy_compat import _default_role_model, _default_provider_id

from pathlib import Path
from typing import Any

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutionNodeProtocol
from backend.core.execution.llm_execution_contract import (
    LLMExecutionProviderProtocol,
)
from backend.application.planning.workspace_path_normalizer import (
    normalize_workspace_path,
)
from backend.runtime.executors.project_analysis_sampler import (
    ProjectAnalysisSampler,
)
from backend.runtime.executors.project_analysis_prompt import (
    ProjectAnalysisPrompt,
)


class ProjectAnalysisExecutor:
    """
    项目分析执行器（对标 Qoder 工程理解）。

    职责：
        读 RepoWiki + 抽样文件 + 调 LLM 生成 Markdown 报告

    不职责：
        - 文件抽样（ProjectAnalysisSampler）
        - Prompt 构建（ProjectAnalysisPrompt）
    """

    VERSION = "1.1"
    name = "project_analysis"

    def __init__(
        self,
        provider: LLMExecutionProviderProtocol,
    ) -> None:
        if provider is None:
            raise ValueError("llm provider required")
        self.provider = provider
        self.sampler = ProjectAnalysisSampler()
        self.prompt_builder = ProjectAnalysisPrompt()
        self.execution_count = 0

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> dict[str, object]:
        workspace = self._resolve_workspace(context)
        root = Path(workspace).expanduser().resolve()
        if not root.is_dir():
            raise RuntimeError(f"workspace not a directory: {root}")

        print(f"[project-analysis] analyzing {root}", flush=True)

        wiki = self._load_repowiki(root)
        samples = self.sampler.sample(root, max_files=12)

        task = (
            node.parameters.get("message")
            or node.parameters.get("instruction")
            or "分析这个项目"
        )
        prompt = self.prompt_builder.build(
            workspace=root, task=task,
            wiki=wiki, samples=samples,
        )

        provider_name = self._ctx(context, "provider") or "ollama"
        model = self._ctx(context, "model") or _default_role_model("code")

        print(
            f"[project-analysis] calling LLM provider={provider_name} "
            f"model={model} prompt_chars={len(prompt)}",
            flush=True,
        )

        response = await self.provider.chat(
            provider=provider_name,
            model=model,
            messages=[
                {"role": "system", "content": (
                    "You are a senior software architect. "
                    "Reply in Chinese. Output ONLY a Markdown report. "
                    "No JSON. No code fences."
                )},
                {"role": "user", "content": prompt},
            ],
        )
        report = str(response).strip()
        rel_report = ".biancheng/reports/analysis.md"
        self.execution_count += 1

        print(
            f"[project-analysis] report ready len={len(report)} "
            f"→ {rel_report}",
            flush=True,
        )

        return {
            "executor": self.name,
            "status": "success",
            "changes": [{
                "file": rel_report,
                "before": "",
                "after": report,
                "reason": "项目分析报告",
            }],
        }

    @staticmethod
    def _resolve_workspace(context: KernelContext) -> str:
        w = getattr(context, "workspace_id", None)
        if not isinstance(w, str) or not w.strip():
            w = context.get("workspace") or context.get("root")
        if not isinstance(w, str) or not w.strip():
            raise RuntimeError("project_analysis workspace required")
        return normalize_workspace_path(w)

    @staticmethod
    def _load_repowiki(root: Path) -> dict[str, str]:
        wiki_dir = root / ".biancheng" / "repowiki"
        out: dict[str, str] = {}
        for name in ("architecture", "modules", "conventions"):
            p = wiki_dir / f"{name}.md"
            if p.exists():
                try:
                    out[name] = p.read_text(
                        encoding="utf-8", errors="ignore"
                    )[:3000]
                except OSError:
                    pass
        return out

    @staticmethod
    def _ctx(context: KernelContext, key: str) -> str | None:
        v = getattr(context, key, None)
        if isinstance(v, str) and v.strip():
            return v.strip()
        v = context.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
        return None

    def ready(self) -> bool:
        return self.provider is not None

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "sampler": self.sampler.dump(),
            "prompt_builder": self.prompt_builder.dump(),
        }


__all__ = ["ProjectAnalysisExecutor"]
