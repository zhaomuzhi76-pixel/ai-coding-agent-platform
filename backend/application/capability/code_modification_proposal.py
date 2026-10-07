from __future__ import annotations

from typing import Any

from backend.application.capability.code_modification_proposal_parser import (
    CodeModificationProposalParser,
)
from backend.application.capability.code_modification_proposal_prompt import (
    CodeModificationProposalPrompt,
)
from backend.application.capability.code_modification_proposal_support import (
    CodeModificationProposalSupport,
)
from backend.application.provider_gateway import (
    ApplicationProviderGatewayProtocol,
)


class CodeModificationProposal:
    """
    Generate a generic batch edit proposal via LLM.

    Returns {"kind", "text"} — the executor applies it to every file.
    """

    VERSION = "7.0"
    CAPABILITY_KEY = "application.code_modification.propose:1.0"

    def __init__(
        self,
        provider: ApplicationProviderGatewayProtocol,
    ) -> None:
        self.support = CodeModificationProposalSupport()
        self.support.require_provider(provider)
        self.provider = provider
        self.parser = CodeModificationProposalParser()
        self.prompt = CodeModificationProposalPrompt()
        self.execution_count = 0
        self.failure_count = 0

    async def propose(
        self,
        *,
        task: str,
        file: str,
        source: str,
        provider: str,
        model: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, object]:
        self.support.validate(task, file, source, provider, model)

        try:
            system_prompt = (
                "You are a code editor. Reply with ONLY a JSON object. "
                "No markdown, no explanation, no code fences."
            )
            user_prompt = self.prompt.build(
                task=task,
                file=file,
                source=source,
                context=context,
            )

            print(
                f"[DIAG-PROPOSAL] calling LLM provider={provider!r} "
                f"model={model!r} source_len={len(source)} "
                f"user_prompt_len={len(user_prompt)}",
                flush=True,
            )
            print(
                f"[DIAG-PROPOSAL] user_prompt head: {user_prompt[:200]!r}",
                flush=True,
            )

            raw = await self.provider.chat(
                provider=provider,
                model=model,
                format="json",
                temperature=0.0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            print(
                f"[DIAG-PROPOSAL] LLM raw response len="
                f"{len(raw) if isinstance(raw, str) else type(raw)}",
                flush=True,
            )
            if isinstance(raw, str):
                print(
                    f"[DIAG-PROPOSAL] first 300 chars: {raw[:300]!r}",
                    flush=True,
                )

            proposal = self.parser.parse(raw, file=file, source=source)

            self.execution_count += 1

            return {
                "file": file,
                "kind": proposal["kind"],
                "text": proposal["text"],
            }
        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return (
            self.provider.ready()
            and self.parser.ready()
            and self.prompt.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "capability": self.CAPABILITY_KEY,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
        }


__all__ = ["CodeModificationProposal"]
