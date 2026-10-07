#!/bin/bash
# 只读检测 Ollama 实例状态（不改任何东西）
# 用法：bash scripts/check_ollama_instances.sh
set +e

echo "════════ Ollama 实例检测 ════════"

echo ""
echo "[1] 监听端口 (1143x)"
if command -v ss >/dev/null 2>&1; then
    ss -tln 2>/dev/null | grep -E '1143[0-9]' || echo "  （无 11434~11439 监听）"
else
    echo "  （ss 不可用）"
fi

echo ""
echo "[2] ollama serve 进程"
pgrep -af 'ollama serve' 2>/dev/null || echo "  （无 ollama serve 进程）"

echo ""
echo "[3] 各实例 API 健康"
for port in 11434 11435 11436 11437 11438 11439; do
    if curl -s -m 1 "http://127.0.0.1:$port/api/tags" >/dev/null 2>&1; then
        n=$(curl -s -m 1 "http://127.0.0.1:$port/api/tags" | grep -o '"name"' | wc -l)
        echo "  ✅ $port  模型数=$n"
    fi
done

echo ""
echo "[4] Nginx 反代配置检测"
if [ -f /etc/nginx/conf.d/ollama_lb.conf ]; then
    echo "  ✅ /etc/nginx/conf.d/ollama_lb.conf 存在"
else
    echo "  ⚪ 未部署（模板: deploy/nginx_ollama_lb.conf.template）"
fi

echo ""
echo "════════ 检测完成 ════════"
