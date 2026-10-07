#!/usr/bin/env bash
# 工业级启动前置检查：
#   1. 检查所有关键端口
#   2. 检测重复进程
#   3. 检查 Ollama GPU 支持
#   4. 报告健康状态
# 不阻塞启动，只报告问题

set +e   # 不因单个检查失败退出

echo "================================="
echo "  启动前环境检查"
echo "================================="

EXIT_CODE=0

# ─── 1. 端口检查 ───────────────────────────────
echo
echo "[1/4] 端口占用检查"

check_port() {
    local PORT=$1
    local NAME=$2
    local PIDS=$(lsof -ti :"$PORT" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        local COUNT=$(echo "$PIDS" | wc -l)
        if [ "$COUNT" -gt 1 ]; then
            echo "  ⚠️  $PORT ($NAME) 被 $COUNT 个进程占用: $PIDS"
            EXIT_CODE=1
        else
            echo "  ✅ $PORT ($NAME) 被占用 (PID: $PIDS) — 正常"
        fi
    else
        echo "  ⚪ $PORT ($NAME) 空闲"
    fi
}

check_port 9022 "后端"
check_port 11434 "Ollama"
check_port 27017 "MongoDB"
check_port 4173 "Vite"

# ─── 2. 重复进程检查 ─────────────────────────────
echo
echo "[2/4] 重复进程检查"

OLLAMA_COUNT=$(pgrep -f "ollama serve" | wc -l)
echo "  ollama serve 进程数: $OLLAMA_COUNT"
if [ "$OLLAMA_COUNT" -gt 1 ]; then
    echo "  ⚠️  重复 Ollama 实例！PIDs: $(pgrep -f 'ollama serve' | tr '\n' ' ')"
    EXIT_CODE=1
fi

UVICORN_COUNT=$(pgrep -f "uvicorn.*9022" | wc -l)
echo "  uvicorn 进程数: $UVICORN_COUNT"
if [ "$UVICORN_COUNT" -gt 1 ]; then
    echo "  ⚠️  重复 uvicorn 实例！PIDs: $(pgrep -f 'uvicorn.*9022' | tr '\n' ' ')"
    EXIT_CODE=1
fi

# ─── 3. Ollama GPU 检查 ─────────────────────────
echo
echo "[3/4] Ollama GPU 支持检查"

if command -v nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n 1)
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -n 1)
    echo "  GPU: $GPU_NAME (当前利用率: ${GPU_UTIL}%)"

    # 检查是否有 llama-server 子进程（说明模型已加载）
    LLAMA_PID=$(pgrep -f "llama-server" | head -n 1)
    if [ -n "$LLAMA_PID" ]; then
        LLAMA_CMD=$(ps -p "$LLAMA_PID" -o cmd= 2>/dev/null)
        if echo "$LLAMA_CMD" | grep -q "no-mmap"; then
            echo "  ⚠️  llama-server 使用 --no-mmap（内存模式），可能没用 GPU"
            EXIT_CODE=1
        fi
        if echo "$LLAMA_CMD" | grep -qE "n-gpu-layers|-ngl"; then
            NGL=$(echo "$LLAMA_CMD" | grep -oE "n-gpu-layers [0-9]+|ngl [0-9]+" | head -n 1)
            echo "  GPU 层数: $NGL"
        else
            echo "  ⚠️  llama-server 未指定 GPU 层数（可能纯 CPU）"
        fi
    else
        echo "  ⚪ 无 llama-server 进程（模型未加载）"
    fi
else
    echo "  ⚪ 无 NVIDIA 驱动 / nvidia-smi 不可用"
fi

# ─── 4. 最终建议 ────────────────────────────────
echo
echo "[4/4] 结论"

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "  ✅ 环境正常，可安全启动"
else
    echo "  ⚠️  发现问题（见上）"
    echo "     建议手动处理："
    echo "     1. 杀重复 Ollama: sudo pkill -9 ollama && sleep 2 && sudo systemctl restart ollama"
    echo "     2. 若 GPU 未用: 检查 CUDA 驱动 / 重装 GPU 版 Ollama"
fi

exit $EXIT_CODE
