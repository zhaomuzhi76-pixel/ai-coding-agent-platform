#!/usr/bin/env bash
# start_backend.sh — BianCheng AI Agent 后端启动脚本
#   * 前台运行（不后台、不静默）
#   * 端口固定 9022
#   * Ctrl+C 停止
set -u

PORT=9022
ENV_NAME="${BE_ENV:-biancheng_ai-agent}"
PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJ_ROOT" || { echo "✗ 无法进入 $PROJ_ROOT"; exit 1; }

echo "================================="
echo " BianCheng AI Agent Backend Start"
echo "================================="

# ─── 启动前环境检查 ───
if [ -f scripts/preflight_check.sh ]; then
    bash scripts/preflight_check.sh || true
fi

# ─── 启动流程 ───
echo
echo "[1/6] Checking port $PORT..."
PIDS=$(lsof -ti :"$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "Found processes using port $PORT:"
    echo "$PIDS"
    echo "Stopping processes..."
    kill -9 $PIDS 2>/dev/null || true
    sleep 1
else
    echo "Port $PORT is free"
fi

echo "[2/6] Cleaning stale uvicorn processes..."
pkill -9 -f "uvicorn.*$PORT" 2>/dev/null || true

echo "[3/6] Cleaning multiprocessing leftovers..."
pkill -9 -f "backend.__main__:create_process_application" 2>/dev/null || true
pkill -9 -f "multiprocessing.spawn" 2>/dev/null || true
sleep 1

echo "[4/6] Activating conda environment..."
CONDA_BASE="$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")"
ENV_PY="$CONDA_BASE/envs/$ENV_NAME/bin/python"
if [ -x "$ENV_PY" ]; then
    echo "  Using: $ENV_PY"
    PY="$ENV_PY"
else
    echo "  [warn] $ENV_PY 不存在，回退当前 python"
    PY="$(command -v python)"
fi

echo "[5/6] Checking python..."
"$PY" --version 2>&1

echo "[6/6] Starting backend..."
# ─── GPU Governor（默认开启；关闭设 RAG_GPU_GOVERNOR=0）──
export RAG_GPU_GOVERNOR="${RAG_GPU_GOVERNOR:-1}"
export RAG_GPU_GOVERNOR_IDLE_SEC="${RAG_GPU_GOVERNOR_IDLE_SEC:-300}"
export RAG_GPU_GOVERNOR_INTERVAL_SEC="${RAG_GPU_GOVERNOR_INTERVAL_SEC:-60}"
echo "[GPU-GOV] enabled=$RAG_GPU_GOVERNOR idle=${RAG_GPU_GOVERNOR_IDLE_SEC}s interval=${RAG_GPU_GOVERNOR_INTERVAL_SEC}s"
echo

exec "$PY" -m backend
