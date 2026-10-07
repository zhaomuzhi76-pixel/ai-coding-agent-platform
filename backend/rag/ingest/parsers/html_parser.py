"""HTML 解析器。职责：<title> + <h1~h6> + <p> + <li> + <table> → ParsedPage。
不做 JS 渲染（用 requests 拿到的静态 HTML）、不下载资源、不切块。"""
from __future__ import annotations
import os
from typing import Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)

MAX_HTML_BYTES = 8 * 1024 * 1024


class HtmlParser:
    def supports(self, path: str) -> bool:
        p = path.lower()
        return p.endswith(".html") or p.endswith(".htm")

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        stat = os.stat(path)
        if stat.st_size > MAX_HTML_BYTES:
            raise ValueError(
                f"html too large ({stat.st_size} > {MAX_HTML_BYTES})")
        try:
            from bs4 import BeautifulSoup  # type: ignore
        except ImportError as e:
            raise RuntimeError("未安装 beautifulsoup4") from e

        raw = open(path, "r", encoding="utf-8", errors="replace").read()
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        doc_title = title
        if soup.title and soup.title.string:
            doc_title = doc_title or str(soup.title.string).strip()

        pages: list = []
        # 段落级抽取
        for tag in soup.find_all(["h1", "h2", "h3", "h4",
                                    "h5", "h6", "p", "li"]):
            t = (tag.get_text(" ", strip=True) or "").strip()
            if not t:
                continue
            section = tag.name or ""
            pages.append(ParsedPage(text=t, page_no=0, section=section))
        # 表格
        for ti, table in enumerate(soup.find_all("table"), 1):
            rows = []
            for tr in table.find_all("tr"):
                cells = [c.get_text(" ", strip=True)
                         for c in tr.find_all(["td", "th"])]
                rows.append(" | ".join(cells))
            body = "\n".join(rows).strip()
            if body:
                pages.append(ParsedPage(text=body, page_no=0,
                                         section=f"table_{ti}"))

        return SourceDocument(
            path=os.path.abspath(path), source_type=SourceType.HTML,
            title=doc_title or os.path.splitext(
                os.path.basename(path))[0],
            pages=tuple(pages), file_size=stat.st_size,
            meta={"paragraphs": len(pages), **(meta or {})},
        )


def make_html_parser() -> HtmlParser:
    return HtmlParser()


__all__ = ["HtmlParser", "make_html_parser", "MAX_HTML_BYTES"]
