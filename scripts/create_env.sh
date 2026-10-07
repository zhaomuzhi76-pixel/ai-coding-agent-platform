#!/usr/bin/env bash

set -e

ENV_NAME="biancheng_ai-agent"
PYTHON_VERSION="3.11"

echo "========================================"
echo " BianCheng AI Agent Pro"
echo " Conda Environment Installer"
echo "========================================"

if ! command -v conda >/dev/null 2>&1; then
    echo ""
    echo "ERROR:"
    echo "Conda 未安装。"
    echo ""
    echo "请先安装 Miniconda 或 Anaconda。"
    exit 1
fi

echo ""
echo ">>> 更新 conda..."
conda update -n base -c defaults conda -y

if conda env list | awk '{print $1}' | grep -Fxq "${ENV_NAME}"; then
    echo ""
    echo ">>> 环境 ${ENV_NAME} 已存在。"
else
    echo ""
    echo ">>> 创建环境 ${ENV_NAME} ..."
    conda create -y \
        -n "${ENV_NAME}" \
        python=${PYTHON_VERSION}
fi

echo ""
echo ">>> 激活环境..."

source "$(conda info --base)/etc/profile.d/conda.sh"

conda activate "${ENV_NAME}"

echo ""
echo ">>> Python"

python --version

echo ""
echo ">>> 升级 pip"

python -m pip install --upgrade pip setuptools wheel

echo ""
echo ">>> 安装基础依赖"

pip install \
fastapi \
uvicorn[standard] \
websockets \
httpx \
openai \
anthropic \
google-genai \
pydantic \
pydantic-settings \
python-dotenv \
loguru \
orjson \
aiofiles \
python-multipart \
jinja2 \
tiktoken \
rich \
tenacity \
gitpython \
watchdog \
psutil

echo ""
echo ">>> 输出环境信息"

python - <<PY
import sys
import platform

print("="*60)
print("Python :", sys.version)
print("Platform :", platform.platform())
print("="*60)
PY

echo ""
echo ">>> 生成 requirements.txt"

pip freeze | sort > requirements.txt

echo ""
echo "========================================"
echo "安装完成"
echo ""
echo "环境名称：${ENV_NAME}"
echo ""
echo "激活命令："
echo ""
echo "conda activate ${ENV_NAME}"
echo ""
echo "========================================"
