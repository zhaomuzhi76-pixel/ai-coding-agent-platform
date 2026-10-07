"""Run single-agent proposal branch."""
from __future__ import annotations

from typing import Any, Tuple


async def run_single_agent(
    proposal: Any,
    task: str,
    file: str,
    source: str,
    provider: str,
    model: str,
    context: dict,
) -> Tuple[str, str]:
    result = await proposal.propose(
        task=task, file=file, source=source,
        provider=provider, model=model,
        context={k: v for k, v in context.items() if k != "runtime_context"},
    )
    kind = result.get("kind")
    text = result.get("text")
    if not isinstance(kind, str) or not isinstance(text, str):
        raise ValueError("patch kind and text required (V7 contract)")
    return kind, text
