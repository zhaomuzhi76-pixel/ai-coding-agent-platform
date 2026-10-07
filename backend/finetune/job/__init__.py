"""微调任务管理层（L0~L2）。

分层：
  L0（本包）: spec / state / event    纯数据 + 状态机
  L1:         store / runner          持久化 + 执行器
  L2:         manager                 单例 + 生命周期

铁律：
  - L0 只用 stdlib（dataclasses / enum / time / uuid）
  - L0 不依赖 torch / transformers（可在任何环境测试）
  - L0 不做 IO
  - 命名具体化（JobSpec / JobState / JobEvent，避免通用名）
"""
