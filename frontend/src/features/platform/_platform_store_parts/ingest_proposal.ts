/* 从 platform_store.ts 抽出：ingestProposal 实现。 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function ingestProposalImpl(
  self: any,
  payload: {
    proposal_id: string
    task?: string
    plan?: string
    changes?: any[]
    status?: string
  },
): void {
  const p = {
    proposal_id: payload.proposal_id,
    task: payload.task || "",
    plan: payload.plan || "",
    changes: payload.changes || [],
    attempts: 1,
    status: (payload.status as any) || "pending",
    file_count: (payload.changes || []).length,
    created_at: Date.now() / 1000,
    updated_at: Date.now() / 1000,
    error: "",
  }
  const existing = self.state.proposals.findIndex(
    (x: any) => x.proposal_id === p.proposal_id,
  )
  const proposals =
    existing >= 0
      ? self.state.proposals.map((x: any, i: number) => (i === existing ? p : x))
      : [p, ...self.state.proposals]
  self.patch({
    phase: "ready",
    proposals,
    activeProposalId: p.proposal_id,
    stageCursor: 1,
  })
}
