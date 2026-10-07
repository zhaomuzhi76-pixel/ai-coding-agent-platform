#!/bin/bash
# 前端启动脚本（前台运行，实时日志，固定端口 4173）
set -e

PORT=4173
ROOT="/home/computer01/xiangmu02/biancheng_aiagentpro"
FRONTEND="$ROOT/frontend"

echo "=========================================="
echo " 前端启动 (端口 $PORT · 前台运行)"
echo " 项目根: $ROOT"
echo " 按 Ctrl+C 停止"
echo "=========================================="

# ── 1) 释放端口（占用则强杀）────────────────
echo "[1/3] 检测端口 $PORT ..."
PIDS=$(lsof -t -i:$PORT 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    for pid in $PIDS; do
        CMD=$(ps -p "$pid" -o comm= 2>/dev/null || echo "?")
        echo "  占用 PID=$pid ($CMD) → kill -9"
        kill -9 "$pid" 2>/dev/null || true
    done
    sleep 1
    # 二次确认
    if lsof -t -i:$PORT >/dev/null 2>&1; then
        echo "  ❌ 端口 $PORT 仍被占用，请手动检查"
        lsof -i:$PORT
        exit 1
    fi
fi
echo "  ✓ 端口 $PORT 已释放"

# ── 2) 检查目录 ───────────────────────────────
echo "[2/3] 检查目录..."
if [ ! -d "$FRONTEND" ]; then
    echo "  ❌ $FRONTEND 不存在"
    exit 1
fi
if [ ! -d "$FRONTEND/node_modules" ]; then
    echo "  ⚠ node_modules 不存在，安装依赖..."
    cd "$FRONTEND" && npm install
fi
echo "  ✓ 目录就绪"

# ── 3) 前台启动 vite（exec 替换父进程，Ctrl+C 干净退出）──
echo "[3/3] 启动 vite --host 0.0.0.0 --port $PORT ..."
echo "------------------------------------------"
cd "$FRONTEND"
exec npx vite --host 0.0.0.0 --port "$PORT" --strictPort
