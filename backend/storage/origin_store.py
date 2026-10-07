"""原件持久化存储。职责：上传文件落盘 + 按 hash 取回。
存到 ~/.cache/agent_knowledge/files/<prefix>/<hash>.<ext>（项目仓库外）。
不做解析、不索引、不做权限。线程安全。
"""
from __future__ import annotations
import hashlib
import os
import shutil
from pathlib import Path
from threading import RLock
from typing import Optional

DEFAULT_ROOT = os.path.expanduser("~/.cache/agent_knowledge/files")
HASH_ALGO = "sha256"
PREFIX_LEN = 2  # 二级目录长度，防单目录文件过多


def _hash_bytes(content: bytes) -> str:
    h = hashlib.new(HASH_ALGO)
    h.update(content)
    return h.hexdigest()


class OriginStore:
    def __init__(self, root: Optional[str] = None) -> None:
        self._root = Path(root or DEFAULT_ROOT)
        self._lock = RLock()

    @property
    def root(self) -> str:
        return str(self._root)

    def put_bytes(self, content: bytes, *, ext: str = "",
                  original_name: str = "") -> dict:
        """保存 bytes → 返回 {hash, path, size, ext}。同内容幂等。"""
        if not content:
            raise ValueError("empty content")
        ext = (ext or "").lower().lstrip(".")
        h = _hash_bytes(content)
        prefix = h[:PREFIX_LEN]
        with self._lock:
            dir_ = self._root / prefix
            dir_.mkdir(parents=True, exist_ok=True)
            fname = f"{h}.{ext}" if ext else h
            path = dir_ / fname
            if not path.exists():
                tmp = path.with_suffix(path.suffix + ".tmp")
                tmp.write_bytes(content)
                tmp.replace(path)
        return {
            "hash": h, "path": str(path), "size": len(content),
            "ext": ext, "original_name": original_name,
        }

    def put_file(self, src_path: str, *, original_name: str = "") -> dict:
        """从磁盘文件读取并保存。"""
        if not os.path.isfile(src_path):
            raise FileNotFoundError(src_path)
        content = Path(src_path).read_bytes()
        ext = os.path.splitext(src_path)[1]
        return self.put_bytes(content, ext=ext, original_name=original_name)

    def get_path(self, h: str, ext: str = "") -> Optional[str]:
        """按 hash 查原件路径。ext 未知时可传空，会扫描目录。"""
        if not h or len(h) < PREFIX_LEN:
            return None
        prefix = h[:PREFIX_LEN]
        dir_ = self._root / prefix
        if not dir_.is_dir():
            return None
        if ext:
            p = dir_ / f"{h}.{ext.lstrip('.')}"
            return str(p) if p.exists() else None
        # 无 ext → 扫描
        for f in dir_.iterdir():
            if f.stem == h:
                return str(f)
        return None

    def exists(self, h: str) -> bool:
        return self.get_path(h) is not None

    def delete(self, h: str) -> bool:
        p = self.get_path(h)
        if p is None:
            return False
        try:
            os.unlink(p)
            return True
        except OSError:
            return False

    def count(self) -> int:
        n = 0
        if not self._root.exists():
            return 0
        for d in self._root.iterdir():
            if d.is_dir():
                n += sum(1 for _ in d.iterdir())
        return n

    def total_size(self) -> int:
        total = 0
        if not self._root.exists():
            return 0
        for d in self._root.iterdir():
            if d.is_dir():
                for f in d.iterdir():
                    try:
                        total += f.stat().st_size
                    except OSError:
                        pass
        return total


_DEFAULT: Optional[OriginStore] = None


def get_default_origin_store() -> OriginStore:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = OriginStore()
    return _DEFAULT


def set_default_origin_store(s: Optional[OriginStore]) -> None:
    global _DEFAULT
    _DEFAULT = s


__all__ = ["OriginStore", "get_default_origin_store",
           "set_default_origin_store", "DEFAULT_ROOT"]
