import { PlatformStore } from "./platform_store"
import type { PlatformGateway } from "./platform_gateway"

export class PlatformController {
  readonly store: PlatformStore

  constructor(gateway: PlatformGateway) {
    this.store = new PlatformStore(gateway)
  }

  init(): Promise<void> {
    return this.store.loadCatalog()
  }

  setModel(m: string): void {
    this.store.setModel(m)
  }

  setDomain(d: string): void {
    this.store.setDomain(d)
  }

  setActiveProposal(id: string | null): void {
    this.store.setActiveProposal(id)
  }

  ingestProposal(payload: {
    proposal_id: string
    task?: string
    plan?: string
    changes?: any[]
    status?: string
  }): void {
    this.store.ingestProposal(payload)
  }

  startSession(input: {
    workspace: string
    userId: string
    locale: string
    model?: string
  }): Promise<void> {
    return this.store.startSession(input)
  }

  propose(input: { task: string; files: string[] }): Promise<void> {
    return this.store.propose(input)
  }

  approve(): Promise<void> {
    return this.store.approve()
  }

  reject(reason: string): Promise<void> {
    return this.store.reject(reason)
  }

  apply(): Promise<void> {
    return this.store.apply()
  }

  verify(): Promise<void> {
    return this.store.verify()
  }

  learn(): Promise<void> {
    return this.store.learn()
  }

  clearError(): void {
    this.store.clearError()
  }
}
