"""文件监控层：轮询式 + 零依赖。

分层：
  L0~L3: filter / index / pagination / service
  L4（本包）: watch（变更检测 + 事件路由）

铁律：
  - 零外部依赖（用 os.stat mtime，不用 watchfiles）
  - 只报事件，不做 WS 传输（传输层调用方包）
  - 轮询间隔可配置，硬下限 0.5s
"""
