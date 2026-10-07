/**
 * WebSocket / HTTP 路径常量（模块化）。
 *
 * 职责：
 *   - 集中所有 WS / API 路径字符串
 *   - 与 runtime.ts（host / port）解耦，便于 mock / 换路由
 *
 * 不负责：
 *   - 拼接 base URL（用 runtime.ts 的 wsUrl / apiUrl）
 */

// ── WebSocket 路径 ──
export const WS_AGENT = "/ws/agent"
export const WS_TREE = "/ws/tree"
export const WS_TERMINAL = "/ws/terminal"

// ── 常用 API 前缀 ──
export const API_AGENT = "/agent"
export const API_RAG_INGEST = "/rag/ingest"
export const API_CHATBOT = "/chatbot"
export const API_MCP_CLIENT = "/mcp_client"

export const PATHS = {
  ws: { agent: WS_AGENT, tree: WS_TREE, terminal: WS_TERMINAL },
  api: {
    agent: API_AGENT,
    ragIngest: API_RAG_INGEST,
    chatbot: API_CHATBOT,
    mcpClient: API_MCP_CLIENT,
  },
} as const
