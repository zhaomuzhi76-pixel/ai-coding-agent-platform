"""Coder 提示词构建器。

支持单文件/多文件。多文件时把整个调用链的文件内容一起给 LLM，
让它决定改哪几个文件。

工业级：支持 edit（局部替换）和 replace_all（整文件）两种模式。
"""
from __future__ import annotations

from typing import Any

from backend.agent.orchestration.source_trimmer import (
    SourceTrimmer,
)


class CoderPrompt:
    VERSION = "3.0"
    MAX_SHOWN_LINES = 2000
    MAX_FILE_BYTES = 200_000

    def __init__(self) -> None:
        self._trimmer = SourceTrimmer(
            head_lines=25,
            ctx_before=4,
            ctx_after=2,
            max_total_lines=200,
        )

    def build(
        self,
        *,
        task: str,
        primary_file: str,
        primary_source: str,
        related_files: dict[str, str] | None,
        plan: str,
        prior_feedback: str,
        workspace: str,
    ) -> str:
        related = related_files or {}
        blocks: list[str] = []

        blocks.append(self._file_block(
            primary_file, primary_source, task=task))
        for path, src in related.items():
            if path == primary_file:
                continue
            blocks.append(self._file_block(path, src, task=task))

        user_block = self._load_user_block(workspace)

        feedback = ""
        if prior_feedback:
            feedback = (
                "\nPrior reviewer feedback (FIX THIS):\n"
                f"{prior_feedback}\n"
            )

        # ─── 核心：明确教 LLM 用 edit 模式 ───
        rules_and_schema = (
            "Reply with ONLY a JSON object describing changes "
            "across ALL files. NO markdown, NO code fences, "
            "NO explanation.\n\n"
            "JSON SCHEMA (choose ONE of the two modes per change):\n\n"
            "Mode 1 — `replace_all` (for SHORT files or full rewrite):\n"
            "  {\"changes\": [{\"file\": \"a.py\", \"kind\": \"replace_all\", "
            "\"text\": \"<FULL new file content>\"}]}\n\n"
            "Mode 2 — `edit` (PREFERRED for LARGE files, >100 lines):\n"
            "  {\"changes\": [{\"file\": \"a.py\", \"kind\": \"edit\", "
            "\"edits\": [{\"old\": \"<EXACT substring from file>\", "
            "\"new\": \"<replacement>\"}]}]}\n\n"
            "CRITICAL RULES:\n"
            "1. If the target file has MORE THAN 100 LINES, "
            "you MUST use `kind:\"edit\"`. DO NOT output the entire file.\n"
            "2. In `edit` mode, `old` MUST be an EXACT substring "
            "that appears in the file. Copy it VERBATIM including "
            "indentation and quotes.\n"
            "3. You may include MULTIPLE edits in one change: "
            "`edits: [{old, new}, {old, new}, ...]`\n"
            "4. Only include files that ACTUALLY need changing.\n"
            "5. `file` MUST be a relative path shown above.\n"
            "6. Reply with ONLY the JSON. No markdown. No prose.\n"
            "\n"
            "EXAMPLE — for a 500-line file, editing one function:\n"
            "{\"changes\":[{\"file\":\"large.py\",\"kind\":\"edit\","
            "\"edits\":[{\"old\":\"    print(f'func_50: {x}')\","
            "\"new\":\"    logger.info(f'func_50: {x}')\"}]}]}\n"
            "\n"
            "EXAMPLE — for a 20-line file, full rewrite:\n"
            "{\"changes\":[{\"file\":\"small.py\",\"kind\":\"replace_all\","
            "\"text\":\"<full new content>\"}]}\n"
        )

        return (
            f"Task: {task}\n\n"
            f"Primary error file: {primary_file}\n"
            f"Plan: {plan}\n"
            f"{user_block}"
            f"{feedback}\n"
            "Relevant source files:\n\n"
            + "\n".join(blocks)
            + "\n\n" + rules_and_schema
        )

    def _file_block(
        self, path: str, source: str,
        *, task: str = "",
    ) -> str:
        # 智能裁剪：大文件只保留相关符号 + import 区
        r = self._trimmer.trim(source, task)
        body = r.text
        if len(body) > self.MAX_FILE_BYTES:
            body = body[: self.MAX_FILE_BYTES] + (
                f"\n... (truncated at {self.MAX_FILE_BYTES} bytes)"
            )
        header = f"=== {path} ==="
        if r.trimmed:
            header += (
                f" [trimmed: {r.original_lines}→{r.kept_lines} lines"
                + (f", symbols={list(r.hit_symbols)}" if r.hit_symbols else "")
                + "]"
            )
        return f"{header}\n{body}\n"

    @staticmethod
    def _load_user_block(workspace: str) -> str:
        """注入用户偏好（按 workspace 过滤 scope 生效规则）。"""
        try:
            from backend.agent_learning import profile_ops
            block = profile_ops.render_context(
                auto_only=True, limit=20, workspace=workspace,
            )
            if block:
                return block + "\n"
        except Exception as e:
            print(f"[coder_prompt] user_block error: {e}", flush=True)
        return ""

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["CoderPrompt"]
