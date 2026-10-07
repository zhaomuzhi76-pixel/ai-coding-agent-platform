"""LSP server capabilities declaration."""
from __future__ import annotations

from typing import Any, Dict

from backend.lsp.protocol import LSP_VERSION


def text_document_sync() -> Dict[str, Any]:
    return {"openClose": True, "change": 1, "save": {"includeText": False}}


def completion_provider() -> Dict[str, Any]:
    return {
        "triggerCharacters": [".", ":", "/", "@"],
        "resolveProvider": False,
    }


def hover_provider() -> Dict[str, Any]:
    return {"contentFormat": ["markdown", "plaintext"]}


def definition_provider() -> Dict[str, Any]:
    return {"linkSupport": False}


def diagnostic_provider() -> Dict[str, Any]:
    return {"interFileDependencies": False, "workspaceDiagnostics": False}


def code_action_provider() -> Dict[str, Any]:
    return {"codeActionKinds": ["quickfix", "refactor"]}


def build_capabilities() -> Dict[str, Any]:
    return {
        "textDocumentSync": text_document_sync(),
        "completionProvider": completion_provider(),
        "hoverProvider": hover_provider(),
        "definitionProvider": definition_provider(),
        "diagnosticProvider": diagnostic_provider(),
        "codeActionProvider": code_action_provider(),
    }


def build_server_info() -> Dict[str, Any]:
    return {"name": "backend-lsp-server", "version": "1.0.0"}


def build_initialize_result() -> Dict[str, Any]:
    return {
        "capabilities": build_capabilities(),
        "serverInfo": build_server_info(),
        "protocolVersion": LSP_VERSION,
    }


__all__ = [
    "text_document_sync", "completion_provider", "hover_provider",
    "definition_provider", "diagnostic_provider", "code_action_provider",
    "build_capabilities", "build_server_info", "build_initialize_result",
]
