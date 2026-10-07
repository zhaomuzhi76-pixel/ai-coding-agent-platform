"""Run multi-agent orchestration branch."""
from __future__ import annotations

from typing import Any, Tuple


async def run_multi_agent(
    orchestrator: Any,
    gateway: Any,
    router: Any,
    provider: str,
    task: str,
    file: str,
    source: str,
) -> Tuple[str, str, dict]:
    result = await orchestrator.run(
        task=task, file=file, source=source,
        gateway=gateway, router=router, provider=provider,
    )
    if not result.get("success"):
        raise RuntimeError(
            f"multi-agent failed: reason={result.get('reason')} "
            f"error={result.get('error')}"
        )
    patch = result["patch"]
    return patch["kind"], patch["text"], result
