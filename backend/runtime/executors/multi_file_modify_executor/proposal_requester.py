"""Ask provider for a sample proposal and parse before/after."""
from __future__ import annotations

from typing import Any, Tuple


def _parse_sample(result: Any, sample_source: str) -> Tuple[str, str]:
    if not isinstance(result, dict):
        raise TypeError("proposal result must dict")
    changes = result.get("changes")
    if isinstance(changes, list) and changes:
        change = changes[0]
        if not isinstance(change, dict):
            raise TypeError("sample change must dict")
        before = change.get("before", "")
        after = change.get("after", "")
    else:
        replacement = result.get("replacement")
        if not isinstance(replacement, str):
            raise RuntimeError(
                "proposal result missing changes / replacement"
            )
        before = sample_source
        after = replacement
    if not isinstance(after, str):
        raise RuntimeError("sample replacement must str")
    return before, after


async def request_proposal(
    provider: Any,
    task: str,
    sample_path: str,
    sample_source: str,
    instruction: str,
    runtime_context: Any,
    root: str,
    provider_name: str,
    model: str,
) -> Tuple[str, str]:
    result = await provider.execute(
        task=task,
        files=[sample_path],
        context={
            "runtime_context": runtime_context,
            "files": [sample_path],
            "source": sample_source,
            "instruction": instruction or task,
            "changes": {},
            "provider": provider_name,
            "model": model,
            "root": root,
        },
    )
    return _parse_sample(result, sample_source)
