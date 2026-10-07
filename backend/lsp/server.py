"""LspServer: dispatch LSP requests / notifications over a transport."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.excellence.aliyun.completion import CompletionEngine
from backend.excellence.aliyun.rule_review import RuleReviewer
from backend.lsp import protocol as P
from backend.lsp.capabilities import build_initialize_result
from backend.lsp.documents import DocumentStore
from backend.lsp.handlers import (
    handle_completion, handle_diagnostics, handle_hover,
)


class LspServer:
    """Handle LSP method calls against DocumentStore + excellence engines.

    传输层由调用方注入（stdio / memory），本类只做 dispatch。
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        documents: Optional[DocumentStore] = None,
        completion_engine: Optional[CompletionEngine] = None,
        reviewer: Optional[RuleReviewer] = None,
    ) -> None:
        self.documents = documents or DocumentStore()
        self.completions = completion_engine or CompletionEngine()
        self.reviewer = reviewer or RuleReviewer()
        self._initialized = False
        self._shutdown = False

    # ─── dispatch ───────────────────────────────────────────
    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return a JSON-RPC response dict, or None for notifications."""
        if not isinstance(message, dict) or "method" not in message:
            return self._error(
                message.get("id") if isinstance(message, dict) else None,
                P.INVALID_REQUEST, "not an LSP request",
            )
        method = str(message.get("method", ""))
        params = message.get("params") or {}
        req_id = message.get("id")
        is_notification = req_id is None

        if method == P.METHOD_EXIT:
            self._shutdown = True
            return None
        if method == P.METHOD_INITIALIZE:
            return self._result(req_id, self._initialize())
        if method == P.METHOD_INITIALIZED:
            return None
        if method == P.METHOD_SHUTDOWN:
            self._shutdown = True
            return self._result(req_id, None)
        if method == P.METHOD_DID_OPEN:
            return self._did_open(params)
        if method == P.METHOD_DID_CHANGE:
            return self._did_change(params)
        if method == P.METHOD_DID_SAVE:
            return None
        if method == P.METHOD_DID_CLOSE:
            return self._did_close(params)
        if method == P.METHOD_COMPLETION:
            return self._result(req_id, self._completion(params))
        if method == P.METHOD_HOVER:
            return self._result(req_id, self._hover(params))
        if method == P.METHOD_DIAGNOSTIC:
            return self._result(req_id, self._diagnostics(params))
        if is_notification:
            return None
        return self._error(req_id, P.METHOD_NOT_FOUND,
                           f"method not found: {method}")

    # ─── method impls ───────────────────────────────────────
    def _initialize(self) -> Dict[str, Any]:
        self._initialized = True
        return build_initialize_result()

    def _did_open(self, params: Dict[str, Any]) -> None:
        td = params.get("textDocument") or {}
        uri = str(td.get("uri", ""))
        if not uri:
            return None
        self.documents.open(
            uri=uri,
            language_id=str(td.get("languageId", "python")),
            version=int(td.get("version", 0) or 0),
            text=str(td.get("text", "")),
        )
        return None

    def _did_change(self, params: Dict[str, Any]) -> None:
        td = params.get("textDocument") or {}
        uri = str(td.get("uri", ""))
        changes = params.get("contentChanges") or []
        if not uri or not changes:
            return None
        latest = changes[-1]
        text = str(latest.get("text", ""))
        version = td.get("version")
        self.documents.change(
            uri, text,
            version=int(version) if version is not None else None,
        )
        return None

    def _did_close(self, params: Dict[str, Any]) -> None:
        td = params.get("textDocument") or {}
        uri = str(td.get("uri", ""))
        if uri:
            self.documents.close(uri)
        return None

    def _completion(self, params: Dict[str, Any]) -> list:
        return handle_completion(params, self.documents, self.completions)

    def _hover(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return handle_hover(params, self.documents)

    def _diagnostics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        items = handle_diagnostics(params, self.documents, self.reviewer)
        return {"kind": "full", "items": items}

    # ─── response helpers ───────────────────────────────────
    @staticmethod
    def _result(req_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error(req_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": code, "message": message},
        }

    # ─── introspection ──────────────────────────────────────
    def initialized(self) -> bool:
        return self._initialized

    def shutdown(self) -> bool:
        return self._shutdown

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "initialized": self._initialized,
            "documents": self.documents.count(),
        }


__all__ = ["LspServer"]
