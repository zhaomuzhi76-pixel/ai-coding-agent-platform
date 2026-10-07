from __future__ import annotations

from typing import Any


class CodeModificationProposalPrompt:
    """
    Multi-file batch prompt.

    The LLM only picks a GENERIC operation (prepend/append/replace_all)
    that will be applied to EVERY file. It does NOT need to figure out
    a specific line number — that's where small models fail.
    """

    VERSION = "7.0"
    PREVIEW_LINES = 5

    def build(
        self,
        *,
        task: str,
        file: str,
        source: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        lines = source.split("\n")
        total = len(lines)
        head = "\n".join(
            "%4d: %s" % (i + 1, ln)
            for i, ln in enumerate(lines[: self.PREVIEW_LINES])
        )
        tail_start = max(self.PREVIEW_LINES, total - self.PREVIEW_LINES)
        tail = "\n".join(
            "%4d: %s" % (i + 1, ln)
            for i, ln in enumerate(
                lines[tail_start:], start=tail_start
            )
        )

        return (
            "Task (will be applied to MULTIPLE files, not just this one):\n"
            + task + "\n\n"
            "Sample file: " + file + "  (total " + str(total) + " lines)\n\n"
            "First " + str(self.PREVIEW_LINES) + " lines:\n"
            "---\n" + head + "\n---\n\n"
            "Last " + str(self.PREVIEW_LINES) + " lines:\n"
            "---\n" + tail + "\n---\n\n"
            "Reply with ONLY a JSON object describing ONE GENERIC operation\n"
            "that will be applied to EVERY file:\n\n"
            "{\n"
            '  "kind": "prepend" | "append" | "replace_all",\n'
            '  "text": "<new text to add; use \\n for multi-line>"\n'
            "}\n\n"
            "HOW TO CHOOSE kind:\n"
            "  prepend      -> user wants to ADD text at the very TOP of each file\n"
            "                  (keywords: 开头/顶部/最上面/加一行/第一行/insert at top)\n"
            "  append       -> user wants to ADD text at the very BOTTOM of each file\n"
            "                  (keywords: 末尾/最后/底部/append at end)\n"
            "  replace_all  -> user wants to REPLACE the whole file (rare)\n\n"
            "EXAMPLES:\n"
            "  Task: 'add # copyright at the very top of every file'\n"
            '    -> {"kind": "prepend", "text": "# copyright"}\n\n'
            "  Task: 'append # END at the bottom of every file'\n"
            '    -> {"kind": "append", "text": "# END"}\n\n'
            "  Task: 'file header must start with # hello'\n"
            '    -> {"kind": "prepend", "text": "# hello"}\n\n'
            "RULES:\n"
            "1. Output EXACTLY the JSON object. No markdown. No explanation.\n"
            "2. `text` must NOT include line numbers or leading ': '.\n"
            "3. DO NOT output a specific line number. Only 'kind' and 'text'.\n"
            "4. If unsure between prepend and append, prefer prepend."
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["CodeModificationProposalPrompt"]
