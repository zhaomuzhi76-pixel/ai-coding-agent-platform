/** 待处理文件队列（工业级） */
import { Badge } from "../../../app/ui/industrial"

interface Props {
  pending: File[]
  busy: boolean
  embModel: string
  onRemove: (i: number) => void
  onStart: () => void
}

export function UploadQueue({ pending, busy, embModel, onRemove, onStart }: Props) {
  if (pending.length === 0) return null
  return (
    <div className="ind-card" style={{ padding: 12, marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: 10 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>待处理队列</span>
          <Badge tone="info">{pending.length} 个文件</Badge>
        </div>
      </div>

      <div style={{ display: "grid", gap: 6, marginBottom: 12 }}>
        {pending.map((f, i) => (
          <div key={i} className="upd-pending-item">
            <span style={{ flex: 1 }}>📄 {f.name}</span>
            <span className="upd-size">{(f.size / 1024 / 1024).toFixed(2)} MB</span>
            <button onClick={() => onRemove(i)}>移除</button>
          </div>
        ))}
      </div>

      <div className="upd-start-bar">
        <button className="upd-start-btn" onClick={onStart} disabled={busy}>
          {busy ? "启动中…" : `▶ 开始处理（${pending.length}）`}
        </button>
        <span className="upd-start-hint">
          向量模型：<b>{embModel || "默认"}</b>
        </span>
      </div>
    </div>
  )
}

export default UploadQueue
