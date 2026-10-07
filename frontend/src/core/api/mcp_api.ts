import { request } from "../http/http_client"
import type {
  McpDomainInfo,
  McpServerInfo,
  McpSummary,
  McpToolInfo,
} from "../contracts/mcp"

interface Envelope<T> {
  ok: boolean
  data?: T
  error?: { code: string; message: string }
}

async function call<T>(path: string): Promise<T> {
  const payload = await request<Envelope<T>>(path)
  if (!payload.ok || payload.data === undefined) {
    throw new Error(
      payload.error
        ? `${payload.error.code}: ${payload.error.message}`
        : "unknown error",
    )
  }
  return payload.data
}

export const mcpApi = {
  summary(): Promise<McpSummary> {
    return call("/mcp/summary")
  },
  tools(): Promise<{ tools: McpToolInfo[]; count: number }> {
    return call("/mcp/tools")
  },
  servers(): Promise<{ servers: McpServerInfo[]; count: number }> {
    return call("/mcp/servers")
  },
  domains(): Promise<{ domains: McpDomainInfo[]; count: number }> {
    return call("/mcp/domains")
  },
}
