1.项目简介
本项目是一个面向软件研发场景的工业级 AI 编程智能体平台，目标打造类似 Claude Code / Codex 的智能编程助手。平台采用 LLM + Agent Runtime + Context Engineering + Tool Capability + Workspace UI 的整体架构，实现从用户需求输入到 Agent 分析、执行、反馈的完整闭环。

核心特性：

🤖 完整 Agent 执行链路：用户请求 → Context 构建 → Agent 推理 → Tool 调用 → 任务执行 → 结果反馈

🧠 项目级 Context 管理：Workspace、文件上下文、Session 状态、Agent 工作空间关联

🔒 私有化部署：集成本地 Ollama，企业代码数据零外泄风险

📚 RAG 全链路：PDF/TXT/DOCX 解析、混合检索、Rerank、TopK/Score 调优

🛡️ 内容安全防护：输入-模型-输出三层围栏、多轮会话越狱检测、敏感词变体识别

🏭 工业级门禁：自下而上 L0~L6 分层审查、单文件 ≤230 行、零磁盘测试

2. 系统架构
2.1 整体架构图
┌─────────────────────────────────────────────────────────────────────┐
│                     用户交互层 (AI IDE 工作台)                        │
│   Agent 对话 · 项目管理 · 代码编辑 · 文件浏览 · Terminal · Diff Review  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ WebSocket / HTTP
┌────────────────────────────────▼────────────────────────────────────┐
│                         API 网关层 (FastAPI)                          │
│        路由分发 · 中间件 · 并发守卫 · 可观测性 · 限流重试               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                       Agent Runtime 核心引擎                          │
│   Intent Router → Planner → Executor → Verifier → Result Handler    │
│                    Tool Registry · MCP · Plugin System               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌──────────────┬─────────────────┼─────────────────┬─────────────────┐
│ Context 管理  │    RAG 全链路    │   Tool Capability│   内容安全        │
│  Workspace    │  解析·切块·嵌入  │   文件读写·终端   │   输入/输出围栏   │
│  Session      │  混合检索·重排   │   代码分析·MCP    │   多轮会话追踪    │
│  Memory       │  生成·治理       │   知识库检索      │   敏感词变体      │
└──────────────┴─────────────────┴─────────────────┴─────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                        基础设施层                                     │
│   Ollama · Qwen · Vector DB · MongoDB · Redis · /dev/shm 零磁盘       │
└─────────────────────────────────────────────────────────────────────┘
3.自下而上 L0~L6 分层架构
层级	模块	职责	核心文件
L6	质量 + 测试 + 门禁	工业级审查、门限校验	backend/quality/ backend/project_rules/
L5	RAG + 知识 + 微调	检索增强、知识库、LoRA 微调	backend/rag/ backend/knowledge/ backend/finetune/
L4	API + 提供商	HTTP/WS 接口、LLM Provider	backend/api/ backend/providers/
L3	应用层	Agent Loop、编排、能力组合	backend/application/
L2	运行时	执行引擎、DAG、事件总线、插件	backend/runtime/
L1	核心基础设施	Context、DI、生命周期、契约	backend/core/
L0	环境 + 工具	部署、测试环境	scripts/
4.项目结构
ai-coding-agent-platform/
├── backend/                          # Python 后端（2758 个文件）
│   ├── agent/                        # Agent 能力层
│   │   ├── planner/                  # 任务规划（意图识别、复杂度评估、风险分析）
│   │   ├── orchestration/            # 编排（Coder、Reviewer、Planner）
│   │   └── graph/                    # 任务图（DAG 构建、校验）
│   ├── application/                  # 应用层
│   │   ├── agent_loop/               # Agent 主循环
│   │   ├── multi_agent/              # 多智能体协作
│   │   ├── capability/               # 能力系统
│   │   └── composition/              # 组合根
│   ├── api/                          # HTTP/WS 接口
│   ├── core/                         # 核心基础设施（DI、Context、契约）
│   ├── runtime/                      # 运行时引擎（DAG、执行器、插件）
│   ├── rag/                          # RAG 全链路
│   │   ├── ingest/                   # 文档入库（PDF/DOCX/OCR）
│   │   ├── hybrid/                   # 混合检索（BM25 + 向量）
│   │   ├── generation/               # 生成与引用
│   │   └── governance/               # 幻觉检测、质量评估
│   ├── providers/                    # LLM Provider（Ollama/DashScope/OpenAI）
│   ├── finetune/                     # 微调（LoRA/QLoRA/PEFT）
│   ├── quality/                      # 工业级门禁
│   └── project_rules/                # 项目规则（文件大小、层级纯度）
├── frontend/                         # React + TypeScript 前端
│   ├── src/
│   │   ├── app/                      # 应用层（AI IDE 工作台）
│   │   ├── features/                 # 功能模块
│   │   ├── core/                     # 核心（API、WebSocket、主题）
│   │   └── components/               # 通用组件
│   └── e2e/                          # 端到端测试
├── rag_core/                         # RAG 核心（独立可复用）
├── scripts/                          # 部署与运维脚本
├── contracts/                        # 契约文件（版本化 JSON）
└── docs/                             # 文档
5.核心能力
5.1 Agent Runtime 核心执行框架
完整链路：用户请求 → Context 构建 → Agent 推理 → Tool 调用 → 任务执行 → 结果反馈

意图识别：基于 LLM 的任务分类（代码修改、项目分析、文本生成等）

任务规划：自动拆解复杂任务为可执行步骤

工具调用：文件读写、终端执行、代码分析、知识库检索、MCP 远程工具

执行验证：本地验证 + Diff Review + 自动化测试

插件化扩展：Tool Calling、MCP、知识库增强等新增能力全部通过插件实现

5.2 项目级 Context 管理体系
Workspace：项目工作空间，支持多项目管理

文件上下文：文件树索引、增量扫描、Gitignore 解析

Session 状态：会话持久化、历史消息压缩

Agent 工作空间：Agent 与项目、Session 的关联关系

5.3 RAG 全链路
文档解析：PDF（含 OCR）、DOCX、TXT、Markdown、XLSX、PPTX

混合检索：BM25 + 向量检索 + 重排序（Rerank）

参数调优：TopK、Score 阈值、查询改写、上下文压缩

治理体系：幻觉检测、引用溯源、相关性评估、延迟监控

效果评估：Hit Rate、MRR 指标量化

5.4 内容安全防护
输入侧围栏：敏感词检测、变体还原（拼音/谐音/拆字/Emoji）、Prompt 注入检测

输出侧围栏：流式滑动窗口检测、幻觉验证、安全代答

多轮会话安全：跨轮次语义漂移、渐进式越狱、角色锁定检测

合规审计：拦截日志、版本记录、留存 180 天

5.5 本地私有化部署
Ollama 集成：Qwen 系列模型，systemd 开机自启，网络监听

GPU 治理：显存不足自愈、GPU 锁协调、并发推理控制

Provider 扩展：Ollama、DashScope、OpenAI、Anthropic 统一抽象

5.6 工业级测试门禁
自下而上 L0~L6 分层审查：一条命令审查整层，一条命令修复整层

零磁盘测试：所有产物写入 /dev/shm，跑完自动释放

单文件门限：严格 ≤230 行，避免巨型文件

插件化架构：新增能力通过新增文件实现，不修改主链路

分层纯度检查：禁止低层反向依赖高层
7.快速开始
环境要求
Python 3.10+

Node.js 18+

Ollama（已部署 Qwen 模型）

可选：MongoDB、Redis、Qdrant
8.克隆项目
bash
git clone https://github.com/zhaomuzhi76-pixel/ai-coding-agent-platform.git
cd ai-coding-agent-platform
后端启动
bash
8.1# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

8.2# 安装依赖
pip install -r requirements.txt

8.3# 启动后端
bash scripts/start_backend.sh
 8.4 Ollama 模型准备
bash
# 拉取 Qwen 模型
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

8.5# 验证服务
curl http://localhost:11434/api/tags
8.6 前端启动
bash
cd frontend
npm install
npm run dev
访问 http://localhost:5173 即可进入 AI IDE 工作台。
8.7 生产构建
bash
cd frontend
npm run build



