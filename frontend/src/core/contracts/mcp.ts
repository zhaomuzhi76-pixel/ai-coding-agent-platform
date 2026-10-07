export interface McpToolInfo {
  name: string
  description: string
  category: string
  exposed: boolean
  param_count: number
}

export interface McpServerInfo {
  id: string
  name: string
  endpoint: string
  transport: string
  status: string
  tools: number
}

export interface McpDomainInfo {
  name: string
  entity_types: string[]
  terms: number
}

export interface McpSummary {
  local_tools: number
  remote_servers: number
  domains: number
}
