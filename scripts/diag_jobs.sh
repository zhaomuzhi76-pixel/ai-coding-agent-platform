#!/bin/bash
# 职责：诊断 ingest job 状态与 approve 接口行为（只读，不改数据）
BASE="http://127.0.0.1:9022"
J1="job-e5a5cadf8e234f9e"
J2="job-725001cb4d854728"

echo "───────── 1) 查询 job 当前状态 ─────────"
for J in $J1 $J2; do
    echo "▸ $J:"
    curl -s -m 3 "$BASE/api/rag/ingest/jobs/$J" | python3 -m json.tool 2>/dev/null || echo "  ⚠ 接口无响应/非JSON"
done

echo ""
echo "───────── 2) 查询 approve 接口是否存在 ─────────"
curl -s -m 3 -o /dev/null -w "POST /approve → HTTP %{http_code}\n" \
    -X POST "$BASE/api/rag/ingest/jobs/$J1/approve"

echo ""
echo "───────── 3) 查询 RAG 状态总览 ─────────"
curl -s -m 3 "$BASE/api/rag/status" | python3 -m json.tool 2>/dev/null || echo "  ⚠ 无响应"

echo ""
echo "───────── 4) 前端 useJobPolling.ts 定位 ─────────"
find frontend -name "useJobPolling.ts" 2>/dev/null | head -1
