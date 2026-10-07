"""文件树索引层：mtime-keyed 缓存。

分层：
  L0: filter（已落地）
  L1（本包）: index（缓存 + 失效判定）
  L2: pagination

铁律：
  - 只缓存"目录 → 子项列表"，不做递归
  - mtime 变 = 失效（唯一正确性依据）
  - LRU 上限，防内存膨胀
  - 线程内安全（asyncio 单线程天然安全）
"""
