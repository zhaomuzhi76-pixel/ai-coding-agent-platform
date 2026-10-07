import type { Locale } from "./locale"

export type PageKey =
  | "nav.coding"
  | "nav.platform"
  | "nav.models"
  | "nav.finetune"
  | "nav.mcp"
  | "nav.rag"
  | "nav.security"
  | "nav.monitor"
  | "nav.providers"
  | "nav.brand"
  | "nav.connected"
  | "theme.toLight"
  | "theme.toDark"
  | "theme.light"
  | "theme.dark"
  | "platform.title"
  | "platform.subtitle"
  | "platform.kpi.session"
  | "platform.kpi.proposals"
  | "platform.kpi.models"
  | "platform.kpi.domains"
  | "platform.pipeline.propose"
  | "platform.pipeline.approve"
  | "platform.pipeline.apply"
  | "platform.pipeline.verify"
  | "platform.pipeline.learn"
  | "models.title"
  | "models.subtitle"
  | "models.search"
  | "models.sortName"
  | "models.sortContext"
  | "models.sortCost"
  | "models.empty"
  | "finetune.title"
  | "finetune.subtitle"
  | "mcp.title"
  | "mcp.subtitle"
  | "rag.title"
  | "rag.subtitle"
  | "security.title"
  | "security.subtitle"
  | "monitor.title"
  | "monitor.subtitle"
  | "monitor.refresh"
  | "monitor.pause"
  | "monitor.resume"

export const PAGES: Record<Locale, Record<PageKey, string>> = {
  "zh-CN": {
    "nav.coding": "编码",
    "nav.platform": "平台",
    "nav.models": "模型",
    "nav.finetune": "微调",
    "nav.mcp": "工具",
    "nav.rag": "知识库",
  "nav.chatbot": "AI 助手",
    "nav.security": "安全",
    "nav.monitor": "监控",
    "nav.providers": "配置",
    "nav.brand": "工业级编程平台",
    "nav.connected": "后端已连接",
    "theme.toLight": "切换到亮色",
    "theme.toDark": "切换到暗色",
    "theme.light": "亮色",
    "theme.dark": "暗色",
    "platform.title": "AI 编程工作台",
    "platform.subtitle": "三厂优势 · Codex / Claude Code / 阿里云",
    "platform.kpi.session": "会话",
    "platform.kpi.proposals": "提案总数",
    "platform.kpi.models": "可用模型",
    "platform.kpi.domains": "领域",
    "platform.pipeline.propose": "生成提案",
    "platform.pipeline.approve": "用户审批",
    "platform.pipeline.apply": "应用修改",
    "platform.pipeline.verify": "执行验证",
    "platform.pipeline.learn": "记忆学习",
    "models.title": "模型目录",
    "models.subtitle": "前端拉清单 · 用户选择 · 后端不做路由",
    "models.search": "搜索模型 / 能力 / provider",
    "models.sortName": "按名称",
    "models.sortContext": "按上下文",
    "models.sortCost": "按成本",
    "models.empty": "无匹配模型",
    "finetune.title": "微调管理",
    "finetune.subtitle": "LoRA / Prefix Tuning 全流程：数据 → 训练 → 评估 → 部署",
    "mcp.title": "MCP 工具市场",
    "rag.title": "RAG 私有知识库",
    "rag.subtitle": "数据集 → 向量索引 → 检索",
    "mcp.subtitle": "远端 MCP server 接入 · 本地工具暴露 · JSON-RPC 2.0",
    "security.title": "企业安全",
    "security.subtitle": "租户 · 四元 RBAC · 审计日志 · 权限决策",
    "monitor.title": "监控告警",
    "monitor.subtitle": "全链路 tracer · 延迟分位 · 告警规则 · 实时刷新",
    "monitor.refresh": "刷新",
    "monitor.pause": "暂停",
    "monitor.resume": "继续",
  },
  "en-US": {
    "nav.coding": "Coding",
    "nav.platform": "Platform",
    "nav.models": "Models",
    "nav.finetune": "Finetune",
    "nav.mcp": "Tools",
    "nav.rag": "Knowledge",
    "nav.security": "Security",
    "nav.monitor": "Monitor",
    "nav.providers": "Config",
    "nav.brand": "Industrial Coding Platform",
    "nav.connected": "Backend connected",
    "theme.toLight": "Switch to light",
    "theme.toDark": "Switch to dark",
    "theme.light": "Light",
    "theme.dark": "Dark",
    "platform.title": "AI Coding Workbench",
    "platform.subtitle": "Codex · Claude Code · Aliyun",
    "platform.kpi.session": "Session",
    "platform.kpi.proposals": "Proposals",
    "platform.kpi.models": "Models",
    "platform.kpi.domains": "Domains",
    "platform.pipeline.propose": "Propose",
    "platform.pipeline.approve": "Approve",
    "platform.pipeline.apply": "Apply",
    "platform.pipeline.verify": "Verify",
    "platform.pipeline.learn": "Learn",
    "models.title": "Model Catalog",
    "models.subtitle": "Frontend fetches · user selects · no backend routing",
    "models.search": "Search model / capability / provider",
    "models.sortName": "By name",
    "models.sortContext": "By context",
    "models.sortCost": "By cost",
    "models.empty": "No matching model",
    "finetune.title": "Finetune Manager",
    "finetune.subtitle": "LoRA / Prefix Tuning: data → train → eval → deploy",
    "mcp.title": "MCP Tool Market",
    "rag.title": "RAG Knowledge Base",
    "rag.subtitle": "Datasets → Vector Index → Retrieval",
    "mcp.subtitle": "Remote servers · local tools · JSON-RPC 2.0",
    "security.title": "Enterprise Security",
    "security.subtitle": "Tenants · RBAC · Audit · Permission decisions",
    "monitor.title": "Monitoring & Alerts",
    "monitor.subtitle": "Tracer · latency percentiles · alerts · live refresh",
    "monitor.refresh": "Refresh",
    "monitor.pause": "Pause",
    "monitor.resume": "Resume",
  },
}
