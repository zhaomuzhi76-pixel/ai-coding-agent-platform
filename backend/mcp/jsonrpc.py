"""JSON-RPC 2.0 message types and codec."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

JSONRPC_VERSION = "2.0"


@dataclass
class JsonRpcError:
    code: int
    message: str
    data: Any = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            out["data"] = self.data
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JsonRpcError":
        return cls(
            code=int(data.get("code", -32603)),
            message=str(data.get("message", "unknown")),
            data=data.get("data"),
        )


@dataclass
class JsonRpcRequest:
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    id: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": self.id,
            "method": self.method,
            "params": dict(self.params),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JsonRpcRequest":
        return cls(
            method=str(data["method"]),
            params=dict(data.get("params", {})),
            id=data.get("id"),
        )


@dataclass
class JsonRpcResponse:
    id: Any = None
    result: Any = None
    error: Optional[JsonRpcError] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"jsonrpc": JSONRPC_VERSION, "id": self.id}
        if self.error is not None:
            out["error"] = self.error.to_dict()
        else:
            out["result"] = self.result
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JsonRpcResponse":
        err = data.get("error")
        return cls(
            id=data.get("id"),
            result=data.get("result"),
            error=JsonRpcError.from_dict(err) if err else None,
        )


def encode(message: Any) -> str:
    if hasattr(message, "to_dict"):
        payload = message.to_dict()
    else:
        payload = message
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def decode(line: str) -> Dict[str, Any]:
    return json.loads(line)


def is_request(data: Dict[str, Any]) -> bool:
    return "method" in data


def is_response(data: Dict[str, Any]) -> bool:
    return "method" not in data and (
        "result" in data or "error" in data
    )


__all__ = [
    "JSONRPC_VERSION",
    "JsonRpcError",
    "JsonRpcRequest",
    "JsonRpcResponse",
    "encode", "decode", "is_request", "is_response",
]
