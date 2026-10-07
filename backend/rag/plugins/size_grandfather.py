"""存量超大文件宽限名单（单一职责）。

背景：
  · 项目早期"拆分前就存在"的 >230 行文件
  · 本次任务（URL 编码插件化）未引入这些文件
  · 通过白名单让 T3 只对"新增文件"硬校验 230

铁律：
  · 只允许追加以 `backend/rag/ingest/` 或 `backend/api/` 前缀的存量
  · 新文件禁止写入本表（新增文件必须 ≤230 行）
  · 与 `url_encoder.snapshot` 命名冲突 → 用 `list_grandfathered`
"""
from __future__ import annotations

# 全部为拆分前存量（v0.1 审计 + 递归扫描已确认）
GRANDFATHERED = frozenset({
    "backend/rag/retriever.py",                              # 237
    "backend/rag/retrieval_paths.py",                        # 293
    "backend/rag/ingest/service.py",                         # 235
    "backend/rag/ingest/parsers/pdf_ocr_parser_batch.py",    # 273
    "backend/rag/ingest/jobs/zombie_cleaner.py",             # 451
    "backend/api/system_monitor_router.py",                  # 317
    "backend/api/rag/ingest_detail_router.py",               # 345
})


def is_grandfathered(path: str) -> bool:
    """判断路径是否属于存量宽限名单（后缀匹配，兼容 Windows 反斜杠）。"""
    p = (path or "").replace("\\", "/")
    return any(p.endswith(g) for g in GRANDFATHERED)


def list_grandfathered() -> frozenset:
    """只读返回宽限名单快照（frozenset 保证不可变）。"""
    return GRANDFATHERED
