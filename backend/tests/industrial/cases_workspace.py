"""workspace_path + file_ops 单测。"""
from __future__ import annotations

import os
import tempfile

from backend.workspace.workspace_path import (
    normalize_only, resolve, PathOutsideWorkspace,
)
from backend.workspace.file_ops import read_text, write_text, exists

from .framework import Suite, assert_eq, assert_true


suite = Suite("workspace_layer")


@suite.case
def normalize_polluted_unc():
    polluted = (
        "/home/x/y/\\\\wsl.localhost\\Ubuntu-24.04\\home\\u\\proj"
    )
    got = normalize_only(polluted)
    assert_eq(got, "/home/u/proj")
    return got


@suite.case
def normalize_pure_unc():
    p = "\\\\wsl.localhost\\Ubuntu-24.04\\home\\u\\x"
    assert_eq(normalize_only(p), "/home/u/x")


@suite.case
def normalize_windows_drive():
    assert_eq(
        normalize_only(r"C:\Users\me\proj"),
        "/mnt/c/Users/me/proj",
    )


@suite.case
def normalize_passthrough():
    assert_eq(normalize_only("/home/me/x"), "/home/me/x")


@suite.case
def normalize_empty():
    assert_eq(normalize_only(""), "")
    assert_eq(normalize_only(None), "")  # type: ignore


@suite.case
def resolve_relative():
    with tempfile.TemporaryDirectory() as tmp:
        wp = resolve(tmp, "a/b.py")
        assert_eq(str(wp), os.path.join(tmp, "a", "b.py"))


@suite.case
def resolve_rejects_escape():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            resolve(tmp, "../../etc/passwd")
        except PathOutsideWorkspace:
            return "escaped correctly"
        raise AssertionError("should raise PathOutsideWorkspace")


@suite.case
def resolve_embedded_unc():
    root = "/home/computer01/xiangmu02/LiveTalking"
    path = (
        "/home/computer01/xiangmu02/biancheng_aiagentpro/"
        "\\\\wsl.localhost\\Ubuntu-24.04"
        "\\home\\computer01\\xiangmu02\\LiveTalking/unknown.py"
    )
    wp = resolve(root, path)
    assert_true(str(wp).startswith(root), f"resolved={wp}")
    return str(wp)


@suite.case
def file_ops_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        write_text(tmp, "x/y.txt", "hello")
        got = read_text(tmp, "x/y.txt")
        assert_eq(got, "hello")
        assert_true(exists(tmp, "x/y.txt"))
        assert_true(not exists(tmp, "not/there.txt"))
