import { platformApi } from "../../core/api/platform_api"
import type {
  PlatformDomainInfo,
  PlatformModelOption,
  PlatformProposal,
  PlatformSession,
} from "../../core/contracts/platform"

export interface PlatformGateway {
  createSession(input: {
    workspace: string
    user_id: string
    locale: string
    model: string
  }): Promise<PlatformSession>

  propose(input: {
    sessionId: string
    workspace: string
    model: string
    locale: string
    task: string
    files: string[]
  }): Promise<PlatformProposal>

  approve(sessionId: string, proposalId: string): Promise<PlatformProposal>

  reject(
    sessionId: string,
    proposalId: string,
    reason: string,
  ): Promise<PlatformProposal>

  apply(
    sessionId: string,
    proposalId: string,
  ): Promise<{ proposal: PlatformProposal; result: unknown }>

  verify(
    sessionId: string,
    proposalId: string,
    workspace: string,
  ): Promise<{ proposal: PlatformProposal; result: unknown }>

  learn(
    sessionId: string,
    proposalId: string,
  ): Promise<{ proposal_id: string; learned: boolean }>

  listProposals(): Promise<{ items: PlatformProposal[]; count: number }>

  listModels(): Promise<PlatformModelOption[]>

  listDomains(): Promise<PlatformDomainInfo[]>
}

export function createPlatformGateway(): PlatformGateway {
  return {
    createSession: (input) => platformApi.createSession(input),
    propose: (input) =>
      platformApi.propose({
        session_id: input.sessionId,
        workspace: input.workspace,
        model: input.model,
        locale: input.locale,
        task: input.task,
        files: input.files,
      }),
    approve: (s, p) => platformApi.approve(s, p),
    reject: (s, p, r) => platformApi.reject(s, p, r),
    apply: (s, p) => platformApi.apply(s, p),
    verify: (s, p, w) => platformApi.verify(s, p, w),
    learn: (s, p) => platformApi.learn(s, p),
    listProposals: () => platformApi.listProposals(100),
    listModels: async () => {
      const { models } = await platformApi.listModels()
      return models
    },
    listDomains: async () => {
      const { domains } = await platformApi.listDomains()
      return domains
    },
  }
}
