#!/bin/bash
# 职责：把 RAG 插件注入指定主后端 FastAPI app 文件（幂等）
# 用法: bash scripts/attach_rag_to_backend.sh [目标文件]
# 默认目标: backend/assembly/fastapi_application.py
set -e
MARKER="# [rag-embedded-mount]"
TARGET="${1:-backend/assembly/fastapi_application.py}"

echo "🎯 目标文件: $TARGET"

if [ ! -f "$TARGET" ]; then
    echo "❌ 文件不存在: $TARGET"
    echo "💡 可用的 FastAPI app 定义:"
    grep -rnE "FastAPI\(" backend/ --include="*.py" | grep -v "\.bak" | grep -v "/tests/"
    exit 0
fi

if grep -qF "$MARKER" "$TARGET"; then
    echo "✅ RAG 插件已挂载于 $TARGET，跳过（幂等）"
    exit 0
fi

BACKUP="${TARGET}.bak.rag"
[ -f "$BACKUP" ] || { cp "$TARGET" "$BACKUP"; echo "📦 已备份 → $BACKUP"; }

python3 - "$TARGET" <<'PY'
import re, sys
from pathlib import Path

p = Path(sys.argv[1])
src = p.read_text(encoding="utf-8")

# 支持 app / application / api / server 等常见变量名
pat = re.compile(
    r'^([ \t]*)(app|application|api|server|fastapi_app)[ \t]*=[ \t]*FastAPI[ \t]*\(',
    re.MULTILINE
)
m = pat.search(src)
if not m:
    raise SystemExit(f"❌ 未在 {p} 找到 FastAPI app 定义（app/application/api/server）")

indent, var = m.group(1), m.group(2)

# 括号平衡定位语句结束位置
i, depth = m.end() - 1, 0
while i < len(src):
    if src[i] == '(':
        depth += 1
    elif src[i] == ')':
        depth -= 1
        if depth == 0:
            break
    i += 1
nl = src.find('\n', i)
pos = len(src) if nl == -1 else nl

inject = f'''

{indent}# [rag-embedded-mount] 嵌入式挂载 RAG 知识库插件（不修改原有逻辑）
{indent}try:
{indent}    from rag_core.integration import mount_rag as _rag_mount
{indent}    if _rag_mount({var}):
{indent}        import logging as _rag_log
{indent}        _rag_log.getLogger(__name__).info("[rag-embedded] RAG 知识库路由已挂载")
{indent}except Exception as _rag_e:
{indent}    import logging as _rag_log
{indent}    _rag_log.getLogger(__name__).warning("[rag-embedded] 挂载失败: %s", _rag_e)
'''
p.write_text(src[:pos] + inject + src[pos:], encoding="utf-8")
print(f"✅ 已注入 RAG 挂载代码 → {p} (app 变量: {var})")
PY

echo "✅ 挂载完成。重启主后端即可生效。"
echo "   回滚: mv $BACKUP $TARGET"
