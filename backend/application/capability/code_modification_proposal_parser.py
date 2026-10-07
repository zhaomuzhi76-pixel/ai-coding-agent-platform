from __future__ import annotations

import json


class CodeModificationProposalParser:
    """
    Parse a generic batch operation from LLM.

    Contract (V7):
        {"kind": "prepend" | "append" | "replace_all", "text": "..."}

    兼容老 V6 (operation/line/new_content) 以防 LLM 偶尔回退。
    """

    VERSION = "7.0"

    BATCH_KINDS = frozenset({"prepend", "append", "replace_all"})

    def parse(
        self,
        raw: object,
        *,
        file: str,
        source: str,
    ) -> dict[str, object]:
        print("[parser-enter]", flush=True)
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("empty proposal response")

        payload = self._decode(raw.strip())
        print(f"[parser-payload] {payload}", flush=True)

        # V7 路径：kind + text
        kind = payload.get("kind")
        if isinstance(kind, str) and kind.strip():
            kind = kind.strip().lower()
            if kind not in self.BATCH_KINDS:
                # 容错映射
                if kind in ("top", "insert_top", "prepend_line", "add_top"):
                    kind = "prepend"
                elif kind in ("bottom", "insert_bottom", "append_line", "add_bottom"):
                    kind = "append"
                else:
                    raise ValueError(
                        f"unsupported kind {kind!r}; "
                        f"expected one of {sorted(self.BATCH_KINDS)}"
                    )

            text = payload.get("text", "")
            if not isinstance(text, str) or not text:
                raise ValueError("text required (non-empty string)")

            print(
                f"[parser-ok] kind={kind} text_len={len(text)}",
                flush=True,
            )
            return {"kind": kind, "text": text}

        # V6 兼容路径：operation + line + new_content
        operation = payload.get("operation")
        if isinstance(operation, str) and operation.strip():
            return self._parse_v6(payload, file=file, source=source)

        raise ValueError(
            "payload must contain either 'kind' (V7) "
            "or 'operation' (V6)"
        )

    def _parse_v6(
        self,
        payload: dict,
        *,
        file: str,
        source: str,
    ) -> dict[str, object]:
        """兼容 V6 的行号模式，转成 batch kind。"""
        operation = str(payload.get("operation", "")).lower()
        new_content = payload.get("new_content", "")
        if not isinstance(new_content, str):
            new_content = ""

        if operation in ("insert_before", "prepend"):
            return {"kind": "prepend", "text": new_content}
        if operation in ("insert_after", "append"):
            return {"kind": "append", "text": new_content}
        if operation in ("replace", "replace_all"):
            return {"kind": "replace_all", "text": new_content}
        if operation == "delete":
            raise ValueError("delete is not supported in batch mode")
        # 兜底
        return {"kind": "prepend", "text": new_content}

    @staticmethod
    def _decode(text: str) -> dict[str, object]:
        if text.startswith("```"):
            text = CodeModificationProposalParser._strip_fence(text)

        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("proposal response must be valid JSON")
            try:
                value = json.loads(text[start:end + 1])
            except json.JSONDecodeError as error:
                raise ValueError(
                    "proposal response must be valid JSON"
                ) from error

        if not isinstance(value, dict):
            raise TypeError("proposal response must object")
        return value

    @staticmethod
    def _strip_fence(text: str) -> str:
        first = text.find("\n")
        last = text.rfind("```")
        if first < 0 or last <= first:
            return text
        return text[first + 1:last].strip()

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["CodeModificationProposalParser"]
