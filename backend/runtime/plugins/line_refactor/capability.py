"""Line Refactor 能力声明。"""
from __future__ import annotations

CAPABILITY = {
    "name": "line_refactor",
    "version": "1.0.0",
    "provides": [
        "line_refactor.plan",
        "line_refactor.render_plan",
        "line_refactor.apply",
    ],
    "layer": "runtime.plugins",
}
