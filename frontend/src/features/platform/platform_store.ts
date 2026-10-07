import type {
  PlatformProposal,
} from "../../core/contracts/platform"
import type { PlatformGateway } from "./platform_gateway"
import {
  initialPlatformState,
  type PlatformState,
} from "./platform_state"

export type PlatformListener = () => void

interface MutationResult {
  proposal: PlatformProposal
}

import { loadCatalogImpl } from "./_platform_store_parts/load_catalog"
import { ingestProposalImpl } from "./_platform_store_parts/ingest_proposal"
export class PlatformStore {
  private readonly gateway: PlatformGateway
  private state: PlatformState = structuredClone(initialPlatformState)
  private listeners = new Set<PlatformListener>()

  constructor(gateway: PlatformGateway) {
    this.gateway = gateway
  }

  getSnapshot(): PlatformState {
    return this.state
  }

  subscribe(listener: PlatformListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private emit(): void {
    this.listeners.forEach((l) => l())
  }

  private patch(partial: Partial<PlatformState>): void {
    this.state = { ...this.state, ...partial }
    this.emit()
  }

  async loadCatalog(): Promise<void> {
    return loadCatalogImpl(this as any)
  }

  setModel(model: string): void {
    this.patch({ selectedModel: model })
  }

  setDomain(domain: string): void {
    this.patch({ selectedDomain: domain })
  }

  setActiveProposal(id: string | null): void {
    this.patch({ activeProposalId: id })
  }

  /** 从 WS done 事件注入 proposal（后端已生成，前端 store 补登记） */
  ingestProposal(payload: {
    proposal_id: string
    task?: string
    plan?: string
    changes?: any[]
    status?: string
  }): void {
    return ingestProposalImpl(this, payload)
  }

  async startSession(input: {
    workspace: string
    userId: string
    locale: string
    model?: string
  }): Promise<void> {
    const model = input.model || this.state.selectedModel
    this.patch({ phase: "working", error: null })
    try {
      const session = await this.gateway.createSession({
        workspace: input.workspace,
        user_id: input.userId,
        locale: input.locale,
        model,
      })
      this.patch({
        phase: "ready",
        session,
        selectedModel: model,
        proposals: [],
        activeProposalId: null,
        stageCursor: 0,
      })
    } catch (error) {
      this.patch({ phase: "error", error: String(error) })
      throw error
    }
  }

  async propose(input: {
    task: string
    files: string[]
  }): Promise<void> {
    const s = this.state.session
    if (!s) throw new Error("no session")
    this.patch({ phase: "working", error: null, stageCursor: 0 })
    try {
      const proposal = await this.gateway.propose({
        sessionId: s.session_id,
        workspace: s.workspace,
        // 优先用「当前 UI 选中」的模型；否则退回 session 里存的
        model: this.state.selectedModel || s.model,
        locale: s.locale,
        task: input.task,
        files: input.files,
      })
      this.patch({
        phase: "ready",
        proposals: [proposal, ...this.state.proposals],
        activeProposalId: proposal.proposal_id,
        stageCursor: 1,
      })
    } catch (error) {
      this.patch({ phase: "error", error: String(error) })
      throw error
    }
  }

  private async mutate(
    action: () => Promise<MutationResult>,
    stage: number,
  ): Promise<void> {
    if (!this.state.activeProposalId) {
      throw new Error("no active proposal")
    }
    const pid = this.state.activeProposalId
    this.patch({ phase: "working", error: null })
    try {
      const { proposal } = await action()
      const proposals = this.state.proposals.map((p) =>
        p.proposal_id === pid ? proposal : p,
      )
      this.patch({ phase: "ready", proposals, stageCursor: stage })
    } catch (error) {
      this.patch({ phase: "error", error: String(error) })
      throw error
    }
  }

  approve(): Promise<void> {
    const s = this.state.session
    const pid = this.state.activeProposalId
    if (!s || !pid) throw new Error("no active proposal")
    return this.mutate(async () => {
      const p = await this.gateway.approve(s.session_id, pid)
      return { proposal: p }
    }, 2)
  }

  reject(reason: string): Promise<void> {
    const s = this.state.session
    const pid = this.state.activeProposalId
    if (!s || !pid) throw new Error("no active proposal")
    return this.mutate(async () => {
      const p = await this.gateway.reject(s.session_id, pid, reason)
      return { proposal: p }
    }, 0)
  }

  apply(): Promise<void> {
    const s = this.state.session
    const pid = this.state.activeProposalId
    if (!s || !pid) throw new Error("no active proposal")
    return this.mutate(async () => {
      const r = await this.gateway.apply(s.session_id, pid)
      return { proposal: r.proposal }
    }, 3)
  }

  verify(): Promise<void> {
    const s = this.state.session
    const pid = this.state.activeProposalId
    if (!s || !pid) throw new Error("no active proposal")
    const workspace = s.workspace
    return this.mutate(async () => {
      const r = await this.gateway.verify(s.session_id, pid, workspace)
      return { proposal: r.proposal }
    }, 4)
  }

  async learn(): Promise<void> {
    const s = this.state.session
    const pid = this.state.activeProposalId
    if (!s || !pid) throw new Error("no active proposal")
    try {
      await this.gateway.learn(s.session_id, pid)
      this.patch({ stageCursor: 5, message: "已学习" })
    } catch (error) {
      this.patch({ error: String(error) })
      throw error
    }
  }

  clearError(): void {
    this.patch({ error: null })
  }
}
