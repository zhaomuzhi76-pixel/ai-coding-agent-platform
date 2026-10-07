"""Layer Audit 能力声明。"""
from __future__ import annotations

CAPABILITY = {
    "name": "layer_audit",
    "version": "1.0.0",
    "provides": [
        "layer_audit.audit",
        "layer_audit.render",
    ],
    "layer": "runtime.plugins",
}
