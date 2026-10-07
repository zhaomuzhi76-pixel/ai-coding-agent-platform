#!/usr/bin/env bash
# start_reranker.sh — Reranker 服务启动（固定端口 9033）
#   * 前台运行（不后台、不静默）
#   * 端口固定 9033，占用则智能释放
#   * Ctrl+C 停止
#   * 幂等：可重复运行
set -u

PORT="${RERANKER_PORT:-9033}"
ENV_NAME="${BE_ENV:-biancheng_ai-agent}"
PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJ_ROOT" || { echo "✗ 无法进入 $PROJ_ROOT"; exit 1; }

echo "=========================================="
echo " Reranker Service (port $PORT)"
echo " 项目根: $PROJ_ROOT"
echo "=========================================="

# ─── [1/5] 端口检查 + 清理 ───
echo
echo "[1/5] Checking port $PORT..."
PIDS=$(lsof -ti :"$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "  占用 PID: $PIDS"
    for pid in $PIDS; do
        CMD=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
        ARGS=$(ps -p "$pid" -o args= 2>/dev/null | head -c 150 || echo "")
        if echo "$CMD $ARGS" | grep -qE "reranker_server|uvicorn|python.*reranker"; then
            echo "  → kill $pid  [$CMD]"
            kill -9 "$pid" 2>/dev/null || true
        else
            echo "  ⚠️  $pid 非 reranker，跳过（避免误杀）：$CMD"
            echo "     请手动处理或改端口：RERANKER_PORT=9034 bash $0"
            exit 1
        fi
    done
    sleep 1
else
    echo "  端口 $PORT 空闲"
fi

# ─── [2/5] 清理残留 ───
echo "[2/5] Cleaning stale reranker processes..."
pkill -9 -f "backend.rag.reranker_server" 2>/dev/null || true
pkill -9 -f "uvicorn.*reranker" 2>/dev/null || true
sleep 1

# ─── [3/5] 检查模型文件 ───
echo "[3/5] Checking model file..."
MODEL="${RERANKER_MODEL:-$HOME/.biancheng/models/reranker/Qwen3-Reranker-4B.Q5_K_M.gguf}"
if [ ! -f "$MODEL" ]; then
    echo "  ❌ 模型缺失: $MODEL"
    echo "     请设置 RERANKER_MODEL 环境变量指向 GGUF 文件"
    exit 1
fi
SIZE=$(du -h "$MODEL" 2>/dev/null | cut -f1)
echo "  ✅ 模型: $MODEL ($SIZE)"

# ─── [4/5] 激活 conda ───
echo "[4/5] Activating conda environment..."
CONDA_BASE="$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")"
ENV_PY="$CONDA_BASE/envs/$ENV_NAME/bin/python"
if [ -x "$ENV_PY" ]; then
    echo "  Using: $ENV_PY"
    PY="$ENV_PY"
else
    echo "  ⚠️  未找到 $ENV_PY，使用系统 python"
    PY="$(command -v python)"
fi

# ─── [5/5] 前台启动（Ctrl+C 停止） ───
echo "[5/5] Starting Reranker..."
echo "  (首次加载模型约 10-20 秒；日志会实时输出)"
echo
export RERANKER_PORT="$PORT"
exec "$PY" -m backend.rag.reranker_server
