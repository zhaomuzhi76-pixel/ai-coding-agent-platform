#!/bin/bash
# 职责：把两个卡死的 pending_review job 标记为 failed（幂等，只读+单次写）
BASE="http://127.0.0.1:9022"
for J in job-e5a5cadf8e234f9e job-725001cb4d854728; do
    echo "▸ 清理 $J ..."
    curl -s -m 3 -X POST "$BASE/api/rag/ingest/jobs/$J/approve" \
        -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null \
        || echo "  ⚠ 无响应（说明 approve 端点还未挂载，请重启 9022）"
done
