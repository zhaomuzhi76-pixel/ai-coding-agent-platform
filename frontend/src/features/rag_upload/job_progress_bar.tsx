/** 进度条。职责：渲染好看的横向进度条 + 百分比。
 * 无数据时显示"处理中..."动画条。 */
import { Badge } from "../../app/ui/industrial"

interface Props {
  status: string
  phase?: string
  current?: number
  total?: number
  message?: string
}

const PHASE_LABEL: Record<string, string> = {
  queued: "排队",
  saving: "保存原件",
  parsing: "OCR 识别",
  chunking: "分块",
  embedding: "向量化",
  indexing: "写入库",
  finalizing: "收尾",
  completed: "完成",
}

export function JobProgressBar({ status, phase, current = 0,
                                 total = 0, message }: Props) {
  const known = total > 0
  const pct = known ? Math.min(100, Math.round(current / total * 100)) : 0
  const label = PHASE_LABEL[phase ?? ""] ?? phase ?? status

  return (
    <div style={{
      flex: 1, minWidth: 200, maxWidth: 420,
      display: "grid", gap: 4,
    }}>
      <div style={{
        display: "flex", justifyContent: "space-between",
        fontSize: 11, opacity: 0.75,
      }}>
        <span><Badge tone="info">{label}</Badge></span>
        <span style={{ fontFamily: "ui-monospace, monospace" }}>
          {known ? `${current}/${total} (${pct}%)` : (message || "处理中…")}
        </span>
      </div>
      <div style={{
        height: 6, borderRadius: 3, overflow: "hidden",
        background: "rgba(118,169,255,.12)",
        position: "relative",
      }}>
        {known ? (
          <div style={{
            height: "100%", width: `${pct}%`,
            background: "linear-gradient(90deg, #4a7bd4, #7aa2f7)",
            transition: "width .4s ease", borderRadius: 3,
          }} />
        ) : (
          <div style={{
            height: "100%", width: "30%",
            background: "linear-gradient(90deg, transparent, #7aa2f7, transparent)",
            animation: "job-slide 1.6s infinite linear",
          }} />
        )}
      </div>
    </div>
  )
}
