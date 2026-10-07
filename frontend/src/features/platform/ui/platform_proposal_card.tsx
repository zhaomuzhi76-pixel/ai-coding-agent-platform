import type { PlatformProposal } from "../../../core/contracts/platform"
import { PlatformStatusBadge } from "./platform_status_badge"

export function PlatformProposalCard(props: {
  proposal: PlatformProposal
  active: boolean
  onSelect: (id: string) => void
}) {
  const { proposal, active, onSelect } = props
  return (
    <div
      className={
        "proposal-card" + (active ? " proposal-card--active" : "")
      }
      onClick={() => onSelect(proposal.proposal_id)}
    >
      <div className="proposal-card__head">
        <span className="proposal-card__id">
          {proposal.proposal_id}
        </span>
        <PlatformStatusBadge status={proposal.status} />
      </div>
      <div className="proposal-card__task">
        {proposal.task}
      </div>
      <div className="proposal-card__meta">
        <span>{proposal.file_count} 文件</span>
        <span>{proposal.changes.length} 变更</span>
        <span>尝试 {proposal.attempts} 次</span>
      </div>
    </div>
  )
}
