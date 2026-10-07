import { request } from "../http/http_client"
import type {
  PlatformDomainInfo,
  PlatformModelOption,
  PlatformProposal,
  PlatformSession,
} from "../contracts/platform"

interface Envelope<T> {
  ok: boolean
  data?: T
  error?: { code: string; message: string; detail?: string }
}

async function call<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const payload = await request<Envelope<T>>(path, init)
  if (!payload.ok || payload.data === undefined) {
    const err = payload.error
    const msg = err ? `${err.code}: ${err.message}` : "unknown error"
    throw new Error(msg)
  }
  return payload.data
}

export const platformApi = {
  createSession(input: {
    workspace: string
    user_id?: string
    locale?: string
    model: string
  }): Promise<PlatformSession> {
    return call<PlatformSession>("/platform/sessions", {
      method: "POST",
      body: JSON.stringify(input),
    })
  },

  getSession(sessionId: string): Promise<PlatformSession> {
    return call<PlatformSession>(
      `/platform/sessions/${sessionId}`,
      { method: "GET" },
    )
  },

  propose(input: {
    session_id: string
    task: string
    files: string[]
    workspace: string
    model: string
    locale?: string
  }): Promise<PlatformProposal> {
    return call<PlatformProposal>("/platform/propose", {
      method: "POST",
      body: JSON.stringify(input),
    })
  },

  approve(
    sessionId: string,
    proposalId: string,
  ): Promise<PlatformProposal> {
    return call<PlatformProposal>("/platform/approve", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        proposal_id: proposalId,
      }),
    })
  },

  reject(
    sessionId: string,
    proposalId: string,
    reason = "",
  ): Promise<PlatformProposal> {
    return call<PlatformProposal>("/platform/reject", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        proposal_id: proposalId,
        reason,
      }),
    })
  },

  apply(
    sessionId: string,
    proposalId: string,
  ): Promise<{ proposal: PlatformProposal; result: unknown }> {
    return call("/platform/apply", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        proposal_id: proposalId,
      }),
    })
  },
  applyAsync(
    proposalId: string,
  ): Promise<{ task_id: string; proposal_id: string; status: string }> {
    return call("/platform/apply?wait=false", {
      method: "POST",
      body: JSON.stringify({ proposal_id: proposalId }),
    })
  },


  verify(
    sessionId: string,
    proposalId: string,
    workspace: string,
  ): Promise<{ proposal: PlatformProposal; result: unknown }> {
    return call("/platform/verify", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        proposal_id: proposalId,
        workspace,
      }),
    })
  },

  learn(
    sessionId: string,
    proposalId: string,
  ): Promise<{ proposal_id: string; learned: boolean }> {
    return call("/platform/learn", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        proposal_id: proposalId,
      }),
    })
  },

  listProposals(limit = 100): Promise<{ items: PlatformProposal[]; count: number }> {
    return call(`/platform/proposals?limit=${limit}`, { method: "GET" })
  },

  listModels(): Promise<{ models: PlatformModelOption[] }> {
    return call("/platform/models", { method: "GET" })
  },

  listDomains(): Promise<{ domains: PlatformDomainInfo[] }> {
    return call("/platform/domains", { method: "GET" })
  },
}
