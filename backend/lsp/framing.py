"""LSP Content-Length framing (unique to LSP; MCP uses newline).

职责边界：
    mcp.jsonrpc  -> JSON-RPC 2.0 消息体（请求/响应/通知）
    framing      -> 只做 Content-Length header 编解码
"""
from __future__ import annotations

from typing import Optional, Tuple

HEADER_SEP = b"\r\n\r\n"
CONTENT_LENGTH = "Content-Length"


def encode_frame(payload: str) -> bytes:
    if not isinstance(payload, str):
        raise TypeError("payload must str")
    data = payload.encode("utf-8")
    header = f"{CONTENT_LENGTH}: {len(data)}\r\n\r\n".encode("ascii")
    return header + data


def parse_headers(header_block: bytes) -> dict:
    out: dict = {}
    for line in header_block.split(b"\r\n"):
        if not line:
            continue
        try:
            text = line.decode("ascii")
        except UnicodeDecodeError:
            continue
        if ":" not in text:
            continue
        key, _, value = text.partition(":")
        out[key.strip().lower()] = value.strip()
    return out


def content_length(headers: dict) -> Optional[int]:
    raw = headers.get(CONTENT_LENGTH.lower())
    if raw is None:
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


def split_frame(buffer: bytes) -> Tuple[Optional[bytes], bytes]:
    """Return (payload_bytes, remaining_buffer). payload None if incomplete."""
    idx = buffer.find(HEADER_SEP)
    if idx < 0:
        return None, buffer
    header_block = buffer[:idx]
    rest = buffer[idx + len(HEADER_SEP):]
    headers = parse_headers(header_block)
    length = content_length(headers)
    if length is None:
        return None, b""
    if len(rest) < length:
        return None, buffer
    return rest[:length], rest[length:]


__all__ = [
    "HEADER_SEP", "CONTENT_LENGTH",
    "encode_frame", "parse_headers", "content_length", "split_frame",
]
