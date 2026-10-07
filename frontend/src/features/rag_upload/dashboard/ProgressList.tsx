import { Badge } from "../../../app/ui/industrial"
import { UploadProgressDetail } from "./UploadProgressDetail"

export interface ItemState {
  jobId: string
  filename: string
  sizeBytes: number
  status: string
  progress?: { phase: string; current: number; total: number; percent: number }
  error?: string
  chunks: number
  elapsedMs: number
}

interface Props {
  items: ItemState[]
  onCancel: (jobId: string) => void         // 生成中 → 取消
  onDeleteVectors: (jobId: string) => void  // 已完成 → 删向量
  onClear: (jobId: string) => void          // 仅清卡片
  onDetail: (jobId: string) => void
}

export function ProgressList({
  items, onCancel, onDeleteVectors, onClear, onDetail,
}: Props) {
  if (items.length === 0) return null
  const active = items.filter((i) =>
    ["pending", "running", "pending_review"].includes(i.status)).length

  return (
    <div className="ind-card" style={{ padding: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: 10 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>处理进度</span>
          <Badge tone="info">{items.length} 个</Badge>
          {active > 0 && <Badge tone="warning">{active} 进行中</Badge>}
        </div>
      </div>
      <div style={{ display: "grid", gap: 6 }}>
        {items.map((it, i) => (
          <UploadProgressDetail
            key={`${it.jobId}-${i}`}
            filename={it.filename}
            sizeBytes={it.sizeBytes}
            progress={it.progress}
            elapsedMs={it.elapsedMs}
            status={it.status}
            chunks={it.chunks}
            error={it.error}
            onCancel={() => onCancel(it.jobId)}
            onDeleteVectors={() => onDeleteVectors(it.jobId)}
            onClear={() => onClear(it.jobId)}
            onDetail={() => onDetail(it.jobId)}
          />
        ))}
      </div>
    </div>
  )
}
export default ProgressList
