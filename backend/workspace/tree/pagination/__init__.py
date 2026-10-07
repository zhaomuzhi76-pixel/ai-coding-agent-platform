"""文件树分页 + 流式层。

分层：
  L0: filter
  L1: index
  L2（本包）: pagination（cursor + streamer）
  L3: file_tree_service

铁律：
  - 游标基于 name（稳定），不用数字索引
  - limit 有硬上限（防 DoS）
  - streamer 是 async generator，非阻塞
  - 零 backend 依赖（只用 stdlib + 同包）
"""
