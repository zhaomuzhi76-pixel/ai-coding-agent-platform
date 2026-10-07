from __future__ import annotations

import hashlib
import re
from typing import Any

from backend.code_intelligence.errors.error_parser import ParsedError


class ErrorSignature:
    """跨项目可复用的错误指纹。"""

    VERSION = "1.1"
    RESPONSIBILITY = ("error_fingerprint",)

    # 引号用十六进制转义，避免 raw string 冲突
    _VALUE = re.compile(
        r"[\x22\x27].*?[\x22\x27]|\b\d+\b|\bNone\b|\bTrue\b|\bFalse\b"
    )
    _IDENT = re.compile(r"\b([a-zA-Z_]\w+)\b")

    KEEP = frozenset({
        "Error", "Exception", "Warning", "Key", "Value", "Type",
        "Index", "Attribute", "Import", "Name", "Syntax",
        "ZeroDivision", "FileNotFound", "Permission", "OS", "IO",
        "Runtime", "Stop", "Overflow", "Assertion", "NotImplemented",
    })

    def compute(self, error: ParsedError) -> str:
        parts = [
            error.format or "unknown",
            self._normalize_type(error.error_type),
            self._normalize_message(error.message),
        ]
        raw = "|".join(parts)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _normalize_type(etype: str) -> str:
        if not etype:
            return "Unknown"
        return etype.split(".")[-1]

    def _normalize_message(self, message: str) -> str:
        if not message:
            return ""
        msg = re.sub(
            r"^\w+(Error|Exception|Warning):\s*", "", message
        )
        msg = self._VALUE.sub("<v>", msg)

        def repl(m: re.Match) -> str:
            return m.group(1) if m.group(1) in self.KEEP else "<id>"

        msg = self._IDENT.sub(repl, msg)
        msg = re.sub(r"\s+", " ", msg).strip()
        return msg[:200]

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = ["ErrorSignature"]
