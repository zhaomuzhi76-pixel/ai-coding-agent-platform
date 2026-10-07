# 微调 Tab 层复盘 (D~R + 4 项改造)

> 归档 2026-09-26 · v1 冻结 (84/84 + 40+ E2E 全绿)

## 能力全景
- 环境检测  GET /api/finetune/env
- 数据集 CRUD  上传/校验/编辑/下载
- 提交训练  POST /jobs (4 项 override)
- 实时事件流  WS /ws/finetune/jobs
- 任务详情 Drawer  历史+实时+指标+一键部署
- 适配器管理  扫描/部署/挂载/拒绝
- 部署全链路  异步 + WS /ws/finetune/deploy/{task_id}
- 训练配置覆盖  num_epochs/batch_size/learning_rate/max_seq_len
- 训练成功自动注册  runner._auto_register_adapter
- Prefix 拒绝  早检 peft_type

## 端到端数据流
提交(+4 override) -> POST /jobs -> JobRunner -> Trainer -> LoRA
    |-- WS 广播 started/log/progress/succeeded
    |-- runner._auto_register_adapter -> registry (SQLite)

[部署到 ollama] -> POST /deploy?wait=false -> task_id
    |-- WS /deploy/{task_id}
        |-- env_bootstrap  ~1.4s
        |-- merge_lora     ~7.2s  主环境 python (peft 0.21 + tf 5.17)
        |-- convert_gguf   ~3.1s  隔离 venv (tf 4.44 + llama.cpp)
        |-- ollama_create  ~2.3s  -> ollama run OK

## 17 个坑
1.  curl 打 8000 (实为 9022)                 先探测端口
2.  _wrap 响应包一层                          看原始 JSON
3.  单引号被 bash -lc '...' 吞                用 << 'END'
4.  data === {type:pong} 被解析成标签         JS 字面量必须带引号
5.  model[tokenizer] 但 model 已是 PeftModel  变量名掩盖语义
6.  warmup_ratio 在 transformers 5.x 移除     inspect 动态过滤
7.  数据 4 字符 < min_chars=10                契约阈值是坑
8.  未读 finetune_page 就加组件 -> 重复 6 个  落地前必先探测
9.  ollama 拒绝 QLoRA ADAPTER                 必须 merge->GGUF->create
10. tf 5.x lazy import 崩 BloomPreTrainedModel 子进程隔离
11. _wrap_async 从未定义                      原生就有 bug
12. pip install --target 降级主环境           禁用, 一律 venv
13. venv 重装 torch 3.5G                      --system-site-packages
14. to_thread 里 SQLite 跨线程 -> 卡死        改同步调用
15. validate 与 train 过滤规则不一致          契约一致
16. _infer_source_job_id 静默失败             幂等 + 真实列名
17. peft 0.21 + tf 4.44 组合不兼容            merge 走主环境

## 架构决策
- QLoRA 部署         merge -> GGUF -> ollama create
- Prefix/Prompt     明确拒绝 (virtual tokens 属输入层)
- merge 环境        主环境 python (peft 0.21 + tf 5.17)
- GGUF 转换         隔离 venv (tf 4.44, 136M, --system-site-packages)
- pip --target      禁用 (会静默改主环境)
- WS 事件           created 落盘; 其余广播
- Deploy            异步 task_id + WS (?wait=true 兼容)
- method 推断       adapter_config.json::peft_type
- validate 契约     与 filter_by_length 一致

## 新增文件

后端 6:
- backend/finetune/deploy/env_bootstrap.py
- backend/finetune/deploy/merger.py
- backend/finetune/deploy/gguf_converter.py
- backend/finetune/deploy/deploy_hub.py
- backend/api/finetune/deploy_ws.py
- backend/finetune/backends/trainer_progress_callback.py

前端 8:
- frontend/src/features/finetune/ui/env_panel.tsx
- frontend/src/features/finetune/ui/dataset_panel.tsx
- frontend/src/features/finetune/ui/metrics_from_events.ts
- frontend/src/features/finetune/ui/job_stream_panel.tsx
- frontend/src/features/finetune/ui/job_selection_bus.ts
- frontend/src/features/finetune/ui/use_finetune_jobs.ts
- frontend/src/features/finetune/ws/deploy_socket.ts
- frontend/src/features/finetune/ui/use_deploy_task.ts

脚本 2:
- scripts/env_snapshot.sh
- .git/hooks/pre-commit

## 环境快照基线

主环境:
  torch 2.14.0+cu126  transformers 5.17.0  peft 0.21.0
  datasets 5.0.1  accelerate 1.15.0  bitsandbytes 0.50.2
  huggingface-hub 1.33.0  tokenizers 0.23.2  safetensors 0.8.0

隔离 venv (~/.biancheng/tf4x-venv):
  transformers 4.44.2  peft 0.21.0(继承)  136 MB

磁盘: ~/.biancheng 2.2G · /tmp 252M

## 质量指标
- 工业回归  84/84
- E2E 断言  40+
- 训练耗时  10~16s
- 部署耗时  14~18s
- TS 编译   exit 0

## 真机验收清单
[x] 环境检测: 可训练 + RTX 4060 + 6 包全绿 + ollama
[x] 数据集: 上传/预校验/短样本警告/编辑/下载/删除
[x] 训练: 4 项 override + 事件流 + 自动注册
[x] 部署: Drawer 一键 + 4 步实时进度 + ollama run
[x] Prefix 类明确拒绝
[x] pre-commit hook 快照

## 升级路径
1. 训练指标持久化 SQLite
2. 多用户并发 (Redis 替换进程内 hub)
3. Prefix 自建推理服务
4. Model Registry 版本化

---
D~R 层开发沉淀 · 17 坑 · 40+ 断言 · 84/84 回归
