import type { Locale } from "./locale"

export type CoreKey =
  | "app.name"
  | "project.workspace"
  | "project.recent"
  | "project.open"
  | "project.create"
  | "project.switch"
  | "project.path"
  | "project.name"
  | "session.active"
  | "agent"
  | "agent.newTask"
  | "agent.running"
  | "tools"
  | "tools.files"
  | "tools.search"
  | "tools.terminal"
  | "tools.mcp"
  | "intelligence"
  | "intelligence.analysis"
  | "modification"
  | "review"
  | "verify"
  | "models"
  | "monitor"
  | "settings"
  | "ready"
  | "notConnected"
  | "locale"
  | "local"
  | "online"

export const CORE: Record<Locale, Record<CoreKey, string>> = {
  "zh-CN": {
    "app.name": "编程 AI Agent",
    "project.workspace": "工作区",
    "project.recent": "最近项目",
    "project.open": "打开项目",
    "project.create": "创建项目",
    "project.switch": "切换项目",
    "project.path": "项目目录",
    "project.name": "项目名称",
    "session.active": "会话已激活",
    agent: "Agent",
    "agent.newTask": "新任务",
    "agent.running": "Agent 正在执行",
    tools: "工具",
    "tools.files": "文件",
    "tools.search": "搜索",
    "tools.terminal": "终端",
    "tools.mcp": "MCP",
    intelligence: "代码智能",
    "intelligence.analysis": "项目分析",
    modification: "代码修改",
    review: "变更审查",
    verify: "验证",
    models: "模型",
    monitor: "监控",
    settings: "设置",
    ready: "就绪",
    notConnected: "尚未连接",
    locale: "语言",
    local: "本地",
    online: "在线",
  },
  "en-US": {
    "app.name": "Biancheng AI Agent",
    "project.workspace": "Workspace",
    "project.recent": "Recent Projects",
    "project.open": "Open Project",
    "project.create": "Create Project",
    "project.switch": "Switch Project",
    "project.path": "Project Path",
    "project.name": "Project Name",
    "session.active": "Session Active",
    agent: "Agent",
    "agent.newTask": "New Task",
    "agent.running": "Agent Running",
    tools: "Tools",
    "tools.files": "Files",
    "tools.search": "Search",
    "tools.terminal": "Terminal",
    "tools.mcp": "MCP",
    intelligence: "Code Intelligence",
    "intelligence.analysis": "Project Analysis",
    modification: "Code Modification",
    review: "Review",
    verify: "Verify",
    models: "Models",
    monitor: "Monitor",
    settings: "Settings",
    ready: "Ready",
    notConnected: "Not connected",
    locale: "Language",
    local: "Local",
    online: "Online",
  },
}
