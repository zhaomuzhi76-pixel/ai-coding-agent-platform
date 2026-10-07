import type { Locale } from "../../../core/i18n/locale"

export type IndustrialCopyKey =
  | "agent"
  | "projects"
  | "intelligence"
  | "models"
  | "settings"
  | "tools"
  | "workspace"
  | "openFolder"
  | "openFile"
  | "scope"
  | "projectRoot"
  | "target"
  | "message"
  | "send"
  | "newTask"
  | "running"
  | "events"
  | "session"
  | "model"
  | "manageModels"
  | "addModel"
  | "saveModel"
  | "editModel"
  | "removeModel"
  | "provider"
  | "modelName"
  | "baseUrl"
  | "apiKey"
  | "local"
  | "online"
  | "language"
  | "ready"
  | "notConnected"
  | "settingsPlaceholder"
  | "toolsPlaceholder"
  | "targetRelative"
  | "directory"
  | "file"
  | "projectRequired"
  | "operationFailed"

const copy: Record<
  IndustrialCopyKey,
  Record<Locale, string>
> = {
  agent: { "zh-CN": "Agent", "en-US": "Agent" },
  projects: { "zh-CN": "项目", "en-US": "Projects" },
  intelligence: {
    "zh-CN": "代码智能",
    "en-US": "Code Intelligence",
  },
  models: { "zh-CN": "模型", "en-US": "Models" },
  settings: { "zh-CN": "设置", "en-US": "Settings" },
  tools: { "zh-CN": "工具", "en-US": "Tools" },
  workspace: { "zh-CN": "工作区", "en-US": "Workspace" },
  openFolder: { "zh-CN": "打开项目", "en-US": "Open Folder" },
  openFile: { "zh-CN": "打开文件", "en-US": "Open File" },
  scope: { "zh-CN": "Agent 范围", "en-US": "Agent Scope" },
  projectRoot: { "zh-CN": "项目路径", "en-US": "Project Root" },
  target: { "zh-CN": "当前目标", "en-US": "Current Target" },
  message: { "zh-CN": "告诉 Agent 要做什么…", "en-US": "Tell the Agent what to do…" },
  send: { "zh-CN": "执行", "en-US": "Run" },
  newTask: { "zh-CN": "新任务", "en-US": "New Task" },
  running: { "zh-CN": "执行中", "en-US": "Running" },
  events: { "zh-CN": "事件", "en-US": "Events" },
  session: { "zh-CN": "会话", "en-US": "Session" },
  model: { "zh-CN": "模型", "en-US": "Model" },
  manageModels: { "zh-CN": "管理模型", "en-US": "Manage Models" },
  addModel: { "zh-CN": "新增模型", "en-US": "Add Model" },
  saveModel: { "zh-CN": "保存模型", "en-US": "Save Model" },
  editModel: { "zh-CN": "编辑模型", "en-US": "Edit Model" },
  removeModel: { "zh-CN": "删除", "en-US": "Remove" },
  provider: { "zh-CN": "Provider", "en-US": "Provider" },
  modelName: { "zh-CN": "模型名称", "en-US": "Model Name" },
  baseUrl: { "zh-CN": "API 地址", "en-US": "Base URL" },
  apiKey: { "zh-CN": "API Key", "en-US": "API Key" },
  local: { "zh-CN": "本地", "en-US": "Local" },
  online: { "zh-CN": "在线", "en-US": "Online" },
  language: { "zh-CN": "语言", "en-US": "Language" },
  ready: { "zh-CN": "就绪", "en-US": "Ready" },
  notConnected: { "zh-CN": "未连接", "en-US": "Not connected" },
  settingsPlaceholder: {
    "zh-CN": "系统设置入口将在此承载。",
    "en-US": "System settings will live here.",
  },
  toolsPlaceholder: {
    "zh-CN": "文件、搜索、终端与 MCP 工具将在此承载。",
    "en-US": "Files, search, terminal and MCP tools will live here.",
  },
  targetRelative: {
    "zh-CN": "相对路径",
    "en-US": "Workspace-relative path",
  },
  directory: { "zh-CN": "文件夹", "en-US": "Directory" },
  file: { "zh-CN": "文件", "en-US": "File" },
  projectRequired: {
    "zh-CN": "请先选择项目并激活会话。",
    "en-US": "Select a project and activate a session first.",
  },
  operationFailed: {
    "zh-CN": "操作失败",
    "en-US": "Operation failed",
  },
}

export function industrialText(
  locale: Locale,
  key: IndustrialCopyKey,
): string {
  return copy[key][locale]
}
