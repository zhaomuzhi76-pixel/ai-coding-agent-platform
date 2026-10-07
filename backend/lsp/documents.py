"""In-memory text document store for LSP."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    uri: str
    language_id: str = "python"
    version: int = 0
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "language_id": self.language_id,
            "version": self.version,
            "length": len(self.text),
        }


class DocumentStore:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._docs: Dict[str, Document] = {}

    def open(self, uri: str, language_id: str = "python",
             text: str = "", version: int = 0) -> Document:
        doc = Document(uri=uri, language_id=language_id,
                       version=version, text=text)
        self._docs[uri] = doc
        return doc

    def change(self, uri: str, text: str,
               version: Optional[int] = None) -> Optional[Document]:
        doc = self._docs.get(uri)
        if doc is None:
            return None
        doc.text = text
        if version is not None:
            doc.version = version
        return doc

    def save(self, uri: str) -> Optional[Document]:
        return self._docs.get(uri)

    def close(self, uri: str) -> None:
        self._docs.pop(uri, None)

    def get(self, uri: str) -> Optional[Document]:
        return self._docs.get(uri)

    def uris(self) -> List[str]:
        return sorted(self._docs.keys())

    def count(self) -> int:
        return len(self._docs)

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "documents": self.count(),
        }


__all__ = ["Document", "DocumentStore"]
