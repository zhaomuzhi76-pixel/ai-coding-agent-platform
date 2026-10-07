import type { PlatformProposalStatus } from "../../../core/contracts/platform"

const LABELS: Record<string, string> = {
  pending: "待审批",
  approved: "已批准",
  rejected: "已拒绝",
  applied: "已应用",
  failed: "失败",
  rolled_back: "已回滚",
}

export function PlatformStatusBadge(props: {
  status: PlatformProposalStatus | string
}) {
  const cls = `status status--${props.status}`
  const label = LABELS[props.status] ?? props.status
  return <span className={cls}>{label}</span>
}
