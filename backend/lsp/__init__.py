"""LSP layer: Language Server Protocol adapter.

职责边界：
    mcp.jsonrpc   -> JSON-RPC 2.0 消息体（复用）
    lsp.framing   -> Content-Length header 帧（LSP 独有）
    lsp.server    -> LSP method dispatch
    lsp.handlers  -> completion / hover / diagnostics 桥接到 excellence
"""
from backend.lsp.protocol import (
    LSP_VERSION,
    METHOD_INITIALIZE, METHOD_SHUTDOWN,
    METHOD_DID_OPEN, METHOD_DID_CHANGE,
    METHOD_COMPLETION, METHOD_HOVER, METHOD_DIAGNOSTIC,
    SUPPORTED_METHODS,
)
from backend.lsp.framing import (
    encode_frame, split_frame, parse_headers, content_length,
)
from backend.lsp.documents import Document, DocumentStore
from backend.lsp.capabilities import build_initialize_result
from backend.lsp.server import LspServer

__all__ = [
    "LSP_VERSION",
    "METHOD_INITIALIZE", "METHOD_SHUTDOWN",
    "METHOD_DID_OPEN", "METHOD_DID_CHANGE",
    "METHOD_COMPLETION", "METHOD_HOVER", "METHOD_DIAGNOSTIC",
    "SUPPORTED_METHODS",
    "encode_frame", "split_frame", "parse_headers", "content_length",
    "Document", "DocumentStore",
    "build_initialize_result",
    "LspServer",
]
