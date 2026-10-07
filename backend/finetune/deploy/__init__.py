"""Adapter 部署层（D5）。

分层：
  L0（本包）: spec / modelfile      纯数据 + Modelfile 生成
  L1:         registry / deployer / mount
  L2:         api

支持两条部署路径：
  A. ollama Modelfile（零 pip 依赖，本机首选）
  B. peft merge（需 torch+peft+transformers）

铁律：
  - L0 只用 stdlib，可零依赖单测
  - L0 不做 IO（生成文本，不写文件）
  - 命名具体化（AdapterSpec / ModelfileSpec）
"""
