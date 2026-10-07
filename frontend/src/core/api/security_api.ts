import { request } from "../http/http_client"
import type {
  CheckResult,
  RoleInfo,
  SecuritySummary,
} from "../contracts/security"

interface Envelope<T> {
  ok: boolean
  data?: T
  error?: { code: string; message: string; detail?: string }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const payload = await request<Envelope<T>>(path, init)
  if (!payload.ok || payload.data === undefined) {
    const msg = payload.error
      ? `${payload.error.code}: ${payload.error.message}`
      : "unknown error"
    throw new Error(msg)
  }
  return payload.data
}

export const securityApi = {
  summary(): Promise<SecuritySummary> {
    return call("/security/summary")
  },
  roles(): Promise<{ roles: RoleInfo[]; count: number }> {
    return call("/security/roles")
  },
  role(name: string): Promise<RoleInfo> {
    return call(`/security/roles/${encodeURIComponent(name)}`)
  },
  check(payload: {
    user_id: string
    tenant_id: string
    roles: string[]
    permission: string
  }): Promise<CheckResult> {
    return call("/security/check", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
}
