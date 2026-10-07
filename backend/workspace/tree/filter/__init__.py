"""文件树过滤器：内置忽略规则 + .gitignore 解析。

分层：
  L0（本包）: builtin_ignores / gitignore_parser
  上层：index（缓存）/ pagination（分页）/ file_tree_service（装配）

铁律：
  - 零 backend 依赖（只用 stdlib）
  - 纯函数式决策（输入路径 → 忽略/保留）
"""
