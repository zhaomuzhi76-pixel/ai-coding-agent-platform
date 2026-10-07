"""模型能力测试报告生成器（L2）。

职责：
    - 把 BenchmarkResult 渲染成人可读的文本报告
    - 分析擅长/不擅长能力
    - 推荐/不推荐使用场景

不负责：
    - 跑测（runner 管）
    - 持久化（store 管）
    - HTTP（api 管）

纯函数：
    - 同 BenchmarkResult → 同报告文本
    - 无 IO / 无副作用

命名具体化：
    render_text / analyze_strengths 等前缀化，避免通用名冲突
\n\nCompat shim. See ._report_parts."""
from __future__ import annotations
from ._report_parts import *  # noqa
from ._report_parts import (BenchmarkCaseResult, BenchmarkResult, Iterable, _BAR_WIDTH, _CATEGORY_LABEL, _LINE, _RATING_LABEL, __all__, _bar, _case_line, _cmap, analyze_strengths, analyze_weaknesses, annotations, avoid_scenarios, recommend_scenarios, render_summary_line, render_text,)  # noqa
