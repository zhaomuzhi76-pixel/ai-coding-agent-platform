"""数据集存储（D4-L1 · 文件 + SQLite 双写）。

职责：
    - 文件：~/.biancheng/datasets/<dataset_id>.jsonl
    - 元数据：~/.biancheng/metrics.db 表 finetune_datasets
    - CRUD 文件 + 元数据

不负责：
    - 内容校验（validator 管）
    - 上传编排（manager 管）
    - HTTP（api 管）

命名具体化：
    save_dataset_file / save_dataset_metadata 等
    避免与 benchmark store / job store 混淆
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from ..spec import (
    DatasetSpec, DatasetFormat,
    DATASET_DIR_NAME, DATASET_ID_PREFIX,
)

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"
_DATASET_DIR = _DB_DIR / DATASET_DIR_NAME

