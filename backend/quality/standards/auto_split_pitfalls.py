"""自动拆分工业级避坑规则（源自 46 文件拆分实战）。

每个 PITFALL 记录一条拆分工具的常见坑：
    症状 → 根因 → 检测方式 → 标准修法

用法：
    from backend.quality.standards.auto_split_pitfalls import PITFALLS
    for p in PITFALLS:
        print(p.name, p.symptom)

    # 一条命令跑自检：
    python -m backend.quality.standards.auto_split_pitfalls
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Pitfall:
    name: str
    symptom: str
    root_cause: str
    detection: str
    fix: str


PITFALLS: List[Pitfall] = [
    Pitfall(
        name="decorator_loss_property",
        symptom="AttributeError: 'function' object has no attribute 'xxx'",
        root_cause="拆分时方法前的 @property 装饰器未复制，属性被当成方法",
        detection="对比 .bak 与 _*_parts/*.py 的方法装饰器差异",
        fix="从 .bak 读所有 @property 方法名，在 mixin 里补回装饰器",
    ),
    Pitfall(
        name="decorator_loss_staticmethod",
        symptom="TypeError: xxx() takes N positional arguments but M were given",
        root_cause="拆分时 @staticmethod 装饰器丢失，方法变成实例方法",
        detection="对比 .bak 里 @staticmethod 修饰的方法名",
        fix="从 .bak 收集 @staticmethod 方法名，扫 _*_parts 补回",
    ),
    Pitfall(
        name="decorator_loss_asynccontextmanager",
        symptom="TypeError: 'async_generator' object does not support the asynchronous context manager protocol",
        root_cause="@asynccontextmanager 丢失，yield 函数变成裸 async_generator",
        detection="扫 async def 有 yield 但无 @asynccontextmanager 的函数",
        fix="补装饰器 + 在文件头 from contextlib import asynccontextmanager",
    ),
    Pitfall(
        name="cross_part_missing_import",
        symptom="NameError: name 'X' is not defined",
        root_cause="mixin*.py 引用了其他 part 里定义的名字，但没 import",
        detection="对每个 part 收集 top 定义，检查其他 part 的 Load 名是否覆盖",
        fix="自动补 from .partN import (X, Y) 到相应 mixin 顶部",
    ),
    Pitfall(
        name="part_main_circular_import",
        symptom="ImportError: cannot import name 'X' from partially initialized module",
        root_cause="part1 → main → mixin1 → part1 形成循环",
        detection="扫 part*.py 里 from .main import，若 main 又 import 该 part → 循环",
        fix="把 from .main import X 改为函数内延迟导入（用到才 import）",
    ),
    Pitfall(
        name="relative_import_level_loss",
        symptom="ModuleNotFoundError: No module named 'cases'",
        root_cause="转导时丢了 ast.ImportFrom.level（. 的个数），相对变绝对",
        detection="对比 part 里的原始 import（含 level）与实际生成的行",
        fix="从 part 里读原始 level，重建为 from ..cases 形式",
    ),
    Pitfall(
        name="parent_dir_index_drift",
        symptom="RuntimeError: yaml loaded no providers (file_not_found)",
        root_cause="Path(__file__).parents[N] 因多一层子目录而算错",
        detection="扫 _*_parts/*.py 里 Path(__file__).resolve().parents[N]",
        fix="N += 1（每多一层 _*_parts 子目录就 +1）",
    ),
    Pitfall(
        name="local_var_leaked_as_prop",
        symptom="ReferenceError: xxx is not defined (前端) / NameError (后端)",
        root_cause="函数内局部变量（for 循环变量 / const 声明）被当顶层名字传给 render",
        detection="AST 扫调用参数，只保留组件函数体 2 空格缩进的定义名",
        fix="用只算函数体顶层定义的正则，剔除非顶层名字",
    ),
    Pitfall(
        name="stmt_placeholder_leaked",
        symptom="ImportError: cannot import name '_stmt_0'",
        root_cause="import / 纯表达式被当作 stmt 编号，泄漏到 __init__.py 导出",
        detection="grep __init__.py 里 _stmt_",
        fix="过滤所有以 _stmt_ 开头的名字",
    ),
    Pitfall(
        name="silent_exception_swallow",
        symptom="客户端收不到帧 / 无日志 / 现象与错误不匹配",
        root_cause="except Exception: pass 静默吞掉异常",
        detection="grep -B1 'except.*:$' | grep -A1 'pass'",
        fix="改为 except Exception as e: print(..., flush=True)",
    ),
    Pitfall(
        name="builtin_shadowed_by_part",
        symptom="TypeError: 'function' object is not subscriptable",
        root_cause="命名空间互注时某个函数名覆盖了 list/dict 等 builtin",
        detection="注入前过滤 builtins.__dict__ 里的名字",
        fix="注入时对 builtin 名字加白名单保护",
    ),
    Pitfall(
        name="sync_function_used_as_await",
        symptom="TypeError: object xxx can't be used in 'await' expression",
        root_cause="拆分后原 async def 变 def（或相反），调用点未同步",
        detection="对比 .bak 与 _*_parts 里函数的 async 修饰",
        fix="从 .bak 恢复 async 修饰符",
    ),
]


def main() -> int:
    """CLI 入口：跑自检 + 打印 PITFALLS 清单。"""
    print("=" * 61)
    print("  自动拆分工业级避坑规则")
    print("=" * 61)
    print()
    print(f"共 {len(PITFALLS)} 条规则：")
    for p in PITFALLS:
        print(f"  [{p.name}]")
        print(f"    症状: {p.symptom}")
        print(f"    修法: {p.fix}")
        print()
    print("=" * 61)
    print("  项目自检")
    print("=" * 61)
    issues = check_all()
    if not issues:
        print("  ✅ 无未修复的坑")
        return 0
    for it in issues:
        print(f"  ⚠️  {it['pitfall']}  发现 {it['count']} 处")
        for f in it["files"]:
            print(f"      {f}")
    return 1


from backend.quality.standards.auto_split_pitfall_checks import (  # noqa: F401,E402
    check_all,
)


__all__ = ["Pitfall", "PITFALLS", "check_all"]


if __name__ == "__main__":
    import sys
    sys.exit(main())
