#!/bin/bash
BASE="http://127.0.0.1:9022/api/rag/ingest/jobs"
for J in job-e5a5cadf8e234f9e job-725001cb4d854728; do
    echo "▸ cancel $J"
    curl -s -m 3 -X POST "$BASE/$J/cancel" | python3 -m json.tool 2>/dev/null \
        || echo "  ⚠ 无响应（后端未重启）"
done
