#!/usr/bin/env bash
# pre-commit hook：只阻止**新增**的 `except Exception: pass`
# 历史遗留不阻塞；未来新代码必须用 swallow()
set +e

STAGED_PY=$(git diff --cached --name-only --diff-filter=AM | grep '\.py$' || true)
[ -z "$STAGED_PY" ] && { echo "✅ silent-guard: 无 py 变更"; exit 0; }

# 统计函数：数出 `except Exception:` 紧跟 `pass` 的次数
count_pattern() {
  awk '
    /^[ \t]*except Exception:[ \t]*$/ { prev=1; next }
    /^[ \t]*pass[ \t]*$/ && prev { c++; prev=0; next }
    { prev=0 }
    END { print c+0 }
  '
}

VIOLATIONS=""
for f in $STAGED_PY; do
  NEW=$(git show ":$f" 2>/dev/null | count_pattern)
  OLD=$(git show "HEAD:$f" 2>/dev/null | count_pattern)
  if [ "${NEW:-0}" -gt "${OLD:-0}" ]; then
    VIOLATIONS="$VIOLATIONS
  - $f  (新增 $((NEW - OLD)) 处)"
  fi
done

if [ -n "$VIOLATIONS" ]; then
  echo "❌ 检出**新增**的 \`except Exception: pass\`"
  echo "   请改用: from backend.core.observability.silent import swallow"
  echo "   模板:   except Exception as e: swallow(\"模块.位置\", e)"
  echo "   违规文件: $VIOLATIONS"
  echo "   如确需静默，请在 except 行上方加注释 # silent-ok"
  exit 1
fi

echo "✅ silent-guard: 通过"
exit 0
