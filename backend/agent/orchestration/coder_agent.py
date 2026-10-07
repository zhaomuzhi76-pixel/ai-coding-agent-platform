from __future__ import annotations
from backend.core.observability.silent import swallow

import json
import re
from typing import Any

from backend.agent.orchestration.contracts import (
    EditContext,
    RoleResult,
)
from backend.agent.orchestration.coder_prompt import CoderPrompt


class CoderAgent:
    """
    Coder: 用 4b 模型生成 patch（可多文件）。

    输入：EditContext（含 primary + related_files）
    输出：RoleResult(data={"changes": [{file, kind, text}, ...]})
    """

    name = "coder"
    version = "2.0"

    SYSTEM_PROMPT = (
        "You are a code editor. Reply with ONLY a JSON object. "
        "No markdown, no explanation, no code fences."
    )

    ALLOWED_KINDS = frozenset({
        "prepend", "append", "replace_all", "edit",
    })

    def __init__(self) -> None:
        self.prompt = CoderPrompt()

    async def run(
        self,
        *,
        context: EditContext,
        gateway: Any,
        router: Any,
        provider: str = "ollama",
        stream_callback: Any = None,
    ) -> RoleResult:
        workspace = str(context.extra.get("workspace", "") or "")
        related = context.extra.get("related_files") or {}

        user_prompt = self.prompt.build(
            task=context.task,
            primary_file=context.file,
            primary_source=context.source,
            related_files=related if isinstance(related, dict) else {},
            plan=context.plan,
            prior_feedback=context.prior_feedback,
            workspace=workspace,
        )
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            if stream_callback is not None:
                # 流式：逐 token 回调
                chunks: list = []
                async for chunk in router.stream_chat(
                    gateway=gateway,
                    task_type="code",
                    provider=provider,
                    messages=messages,
                    format="json",
                    temperature=0.0,
                ):
                    chunks.append(chunk)
                    try:
                        await stream_callback({
                            "event": "token",
                            "role": "coder",
                            "text": chunk,
                        })
                    except Exception as e:
                        swallow("agent.orchestration.coder_agent:84", e, level="error")
                raw = "".join(chunks)
                result = {"model": "stream", "response": raw}
            else:
                result = await router.chat(
                    gateway=gateway,
                    task_type="code",
                    provider=provider,
                    messages=messages,
                    format="json",
                    temperature=0.0,
                )
                raw = str(result["response"])
            changes = self._parse(raw)
            print(
                f"[coder] {len(changes)} changes "
                f"model={result['model']}",
                flush=True,
            )
            return RoleResult(
                role=self.name,
                ok=True,
                data={"changes": changes, "raw": raw},
            )
        except Exception as error:
            return RoleResult(
                role=self.name,
                ok=False,
                data={},
                error=f"{type(error).__name__}: {error}",
            )

    def _parse(self, raw: str) -> list[dict[str, Any]]:
        print(f"[coder-raw] len={len(raw)} preview={raw[:800]!r}", flush=True)
        text = raw.strip()
        if text.startswith("```"):
            first = text.find("\n")
            last = text.rfind("```")
            if first >= 0 and last > first:
                text = text[first + 1:last].strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                raise ValueError("coder response not JSON")
            payload = json.loads(m.group(0))

        changes = payload.get("changes")
        if not isinstance(changes, list) or not changes:
            print(
                f"[coder-payload-fail] payload={payload!r}",
                flush=True,
            )
            raise ValueError("changes must be non-empty list")

        out: list[dict[str, Any]] = []
        for item in changes:
            if not isinstance(item, dict):
                continue
            # 工业级：兼容各模型的字段名变体
            f = (
                item.get("file") or item.get("path")
                or item.get("filename") or item.get("file_path")
            )
            k = (
                item.get("kind") or item.get("change_type")
                or item.get("type") or "replace_all"
            )
            # 归一化 kind 值（兼容 replace_all / replace / modify 等）
            k = str(k).strip().lower()
            if k in ("replace", "modify", "edit", "update"):
                k = "replace_all"
            if k not in self.ALLOWED_KINDS:
                # 未知 kind → 保守用 replace_all（不直接 raise）
                k = "replace_all"
            # edit 模式：只输出 old/new 片段，不输出整文件
            edits = item.get("edits")
            if k == "edit" or (isinstance(edits, list) and edits):
                if not isinstance(edits, list) or not edits:
                    raise ValueError(f"edit mode requires edits list: {item!r}")
                normalized_edits = []
                for e in edits:
                    if not isinstance(e, dict):
                        continue
                    old_frag = e.get("old") or e.get("old_text") or e.get("search")
                    new_frag = e.get("new") or e.get("new_text") or e.get("replace")
                    if not isinstance(old_frag, str) or not old_frag:
                        continue
                    if not isinstance(new_frag, str):
                        new_frag = ""
                    normalized_edits.append({"old": old_frag, "new": new_frag})
                if not normalized_edits:
                    raise ValueError(f"edit mode: no valid edits in {item!r}")
                if not isinstance(f, str) or not f.strip():
                    raise ValueError(f"change.file missing: {item!r}")
                out.append({
                    "file": f.strip(), "kind": "edit",
                    "edits": normalized_edits,
                })
                continue
            t = (
                item.get("text") or item.get("content")
                or item.get("new_content") or item.get("new_text")
            )
            if not isinstance(f, str) or not f.strip():
                raise ValueError(f"change.file missing: {item!r}")
            if not isinstance(t, str) or not t:
                raise ValueError(f"change.text empty: {f!r}")
            out.append({"file": f.strip(), "kind": k, "text": t})

        if not out:
            raise ValueError("no valid changes parsed")
        return out

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
        }


__all__ = ["CoderAgent"]
