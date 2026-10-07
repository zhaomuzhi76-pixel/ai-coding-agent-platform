"""数据集管理（D4）。

分层：
  L0（本包）: spec / validator    纯数据 + 校验
  L1:         storage / manager   文件 + SQLite + 单例
  L2:         api                 HTTP 端点

铁律：
  - L0 只用 stdlib（dataclasses / json / re / pathlib）
  - L0 不做 IO 写操作（只读校验）
  - L0 不依赖 torch / peft
  - 命名具体化（DatasetSpec，避免通用名）

存储：
  文件: ~/.biancheng/datasets/<dataset_id>.jsonl
  元数据: ~/.biancheng/metrics.db 表 finetune_datasets
"""
