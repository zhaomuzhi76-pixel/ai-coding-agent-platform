"""Excel .xlsx 解析器。职责：每行 → "列1: 值1 | 列2: 值2"。
不做 .xls（老格式）、不切块、不索引。
首行为表头；空行跳过；超大文件按行数截断。"""
from __future__ import annotations
import os
from typing import Optional

from backend.rag.ingest.contracts import (
    ParsedPage, SourceDocument, SourceType)

MAX_ROWS_PER_SHEET = 5000  # 防超大表爆内存


class XlsxParser:
    def supports(self, path: str) -> bool:
        return path.lower().endswith(".xlsx")

    def parse(self, path: str, *, title: str = "",
              meta: Optional[dict] = None) -> SourceDocument:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        try:
            import openpyxl  # type: ignore
        except ImportError as e:
            raise RuntimeError("未安装 openpyxl") from e

        wb = openpyxl.load_workbook(path, data_only=True,
                                     read_only=True)
        pages: list = []
        total_rows = 0
        for sn in wb.sheetnames:
            ws = wb[sn]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue
            header = [str(c or "").strip() for c in rows[0]]
            for ri, row in enumerate(rows[1:MAX_ROWS_PER_SHEET + 1], 1):
                cells = []
                for ci, cell in enumerate(row):
                    val = "" if cell is None else str(cell).strip()
                    if not val:
                        continue
                    key = header[ci] if ci < len(header) else f"col{ci + 1}"
                    cells.append(f"{key}: {val}")
                if not cells:
                    continue
                text = " | ".join(cells)
                pages.append(ParsedPage(
                    text=text, page_no=ri,
                    section=f"sheet:{sn}"))
                total_rows += 1
        wb.close()
        stat = os.stat(path)
        return SourceDocument(
            path=os.path.abspath(path), source_type=SourceType.TEXT,
            title=title or os.path.splitext(os.path.basename(path))[0],
            pages=tuple(pages), file_size=stat.st_size,
            meta={"sheets": len(wb.sheetnames), "rows": total_rows,
                  **(meta or {})},
        )


def make_xlsx_parser() -> XlsxParser:
    return XlsxParser()


__all__ = ["XlsxParser", "make_xlsx_parser", "MAX_ROWS_PER_SHEET"]
