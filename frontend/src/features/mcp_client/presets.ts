/** 第三方 MCP Server 预设模板（Dify 风格：点一下自动填充） */

export interface McpPreset {
  id: string
  name: string
  description: string
  icon: string
  transport: "stdio" | "http"
  command?: string
  args?: string[]
  url?: string
  requiresEnv?: string[]   // 需要用户填的环境变量名
}

export const MCP_PRESETS: McpPreset[] = [
  {
    id: "fs",
    name: "Filesystem",
    description: "本地文件读写（受允许目录限制）",
    icon: "📁",
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
  },
  {
    id: "github",
    name: "GitHub",
    description: "仓库 / Issue / PR 操作",
    icon: "🐙",
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-github"],
    requiresEnv: ["GITHUB_PERSONAL_ACCESS_TOKEN"],
  },
  {
    id: "fetch",
    name: "Fetch",
    description: "网页抓取 + Markdown 转换",
    icon: "🌐",
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-fetch"],
  },
  {
    id: "playwright",
    name: "Playwright",
    description: "浏览器自动化（截图 / 点击 / 抓取）",
    icon: "🎭",
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-playwright"],
  },
  {
    id: "sqlite",
    name: "SQLite",
    description: "本地 SQLite 数据库读写",
    icon: "🗄️",
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-sqlite", "/tmp/db.sqlite"],
  },
  {
    id: "memory",
    name: "Memory",
    description: "知识图谱记忆（跨会话持久化）",
    icon: "🧠",
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-memory"],
  },
  {
    id: "sequential-thinking",
    name: "Sequential Thinking",
    description: "结构化推理链（多步思考）",
    icon: "🧩",
    transport: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-sequential-thinking"],
  },
  {
    id: "custom-stdio",
    name: "自定义 stdio",
    description: "自定义本地命令",
    icon: "⚙️",
    transport: "stdio",
    command: "",
    args: [],
  },
  {
    id: "custom-http",
    name: "自定义 HTTP",
    description: "远端 MCP 服务 URL",
    icon: "🔗",
    transport: "http",
    url: "",
  },
]
