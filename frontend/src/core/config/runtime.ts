export interface FrontendRuntimeConfig {
  appName: string
  apiBaseUrl: string
  wsBaseUrl: string
}

const HARDCODED_HOST = "http://127.0.0.1:9022"

function readInjected(): string | null {
  if (typeof window === "undefined") return null
  const w = window as unknown as { __BACKEND_URL__?: string }
  return w.__BACKEND_URL__ && w.__BACKEND_URL__.trim()
    ? w.__BACKEND_URL__.trim().replace(/\/+$/, "")
    : null
}

function build(): FrontendRuntimeConfig {
  const injected = readInjected()
  if (injected) {
    const ws = injected.replace(/^http/, "ws")
    return {
      appName: "Biancheng AI Agent",
      apiBaseUrl: injected + "/api",
      wsBaseUrl: ws + "/ws/agent",
    }
  }

  if (typeof location !== "undefined" && location.protocol === "file:") {
    return {
      appName: "Biancheng AI Agent",
      apiBaseUrl: HARDCODED_HOST + "/api",
      wsBaseUrl: "ws://127.0.0.1:9022/ws/agent",
    }
  }

  // 浏览器环境（Vite dev server 4173）：WebSocket 不能用相对路径，
  // 必须拼出后端绝对地址。API 走 Vite proxy，WS 走直连。
  if (typeof location !== "undefined" && location.hostname) {
    const wsProto = location.protocol === "https:" ? "wss" : "ws"
    // 生产部署在同一域：走同源 /ws
    // 本地开发（Vite 4173）：走后端 9022
    const isDevPort = ["4173", "5173", "3000"].includes(
      location.port || "",
    )
    const wsHost = isDevPort
      ? `${location.hostname}:9022`
      : location.host
    return {
      appName: "Biancheng AI Agent",
      apiBaseUrl: "/api",
      wsBaseUrl: `${wsProto}://${wsHost}/ws/agent`,
    }
  }

  return {
    appName: "Biancheng AI Agent",
    apiBaseUrl: "/api",
    wsBaseUrl: "/ws/agent",
  }
}

export const runtimeConfig: FrontendRuntimeConfig = build()

// ─────────────────────────────────────────────────────────────
// 服务常量（模块化：其他文件不应硬编码 host / port）
// ─────────────────────────────────────────────────────────────

/** 后端端口 */
export const BACKEND_PORT = 9022
/** 本地 Ollama 端口 */
export const OLLAMA_PORT = 11434
/** 前端开发端口（Vite） */
export const FRONTEND_DEV_PORTS = ["4173", "5173", "3000"] as const

/** 本地 Ollama HTTP URL（例如 "http://127.0.0.1:11434"） */
export const OLLAMA_URL = `http://127.0.0.1:${OLLAMA_PORT}`

/** 拼接 WebSocket 绝对地址（wsBaseUrl 是 "ws://host:port/ws/agent" 形态）
 *
 *  用法：
 *    wsUrl(WS_TREE)  -> "ws://127.0.0.1:9022/ws/tree"
 *    wsUrl("/ws/agent")
 */
export function wsUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`
  const root = runtimeConfig.wsBaseUrl.replace(/\/ws\/[^/]+$/, "")
  return `${root}${p}`
}

/** 拼接 HTTP API 绝对地址（apiBaseUrl 是 "http://host:port/api" 形态） */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`
  return `${runtimeConfig.apiBaseUrl}${p}`
}

/** 后端 HTTP 根地址（不含 /api 后缀）
 *  例: "http://127.0.0.1:9022"
 */
export function backendHttpUrl(): string {
  return runtimeConfig.apiBaseUrl.replace(/\/api$/, "")
}

/** 后端 API 根地址（含 /api 后缀）
 *  例: "http://127.0.0.1:9022/api"
 */
export function apiBase(): string {
  return runtimeConfig.apiBaseUrl
}
