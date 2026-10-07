"""模型能力测试系统 · 4 层。

L0: cases.py     用例定义（纯数据，BenchmarkCase）
L0: evaluator.py 判定器（纯函数，Judgment / BenchmarkCaseResult）
L1: runner.py    跑批编排
L2: store.py     结果持久化
L2: report.py    文本报告生成
L3: api.py       HTTP 端点

铁律：
  - L0 只用 stdlib
  - L0 不 import provider 实现（用例与 provider 无关）
  - L0 不做 IO
  - 命名具体化（BenchmarkCase，避免与 quality/tests 层通用名冲突）
"""
