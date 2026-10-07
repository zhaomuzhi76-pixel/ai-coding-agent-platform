#!/usr/bin/env bash
# 环境快照：记录关键包版本，方便对比漂移
set -e
OUT="${1:-/tmp/env_snapshot_$(date +%s).txt}"
python3 -c "
import importlib.metadata as md
pkgs = ['torch','torchvision','transformers','peft','datasets',
        'accelerate','bitsandbytes','huggingface-hub','tokenizers',
        'safetensors','numpy']
for p in pkgs:
    try:
        print(f'{p:20s} {md.version(p)}')
    except md.PackageNotFoundError:
        print(f'{p:20s} (not installed)')
" | tee "$OUT"
echo
echo "snapshot written to $OUT"
