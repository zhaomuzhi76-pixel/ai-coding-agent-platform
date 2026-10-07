/** 上传记录单项。职责：文件名 + 状态 + 进度条 + 操作按钮。 */
import { originUrl } from "../../core/api/rag_upload_api"
import { Badge } from "../../app/ui/industrial"
import { JobProgressBar } from "./job_progress_bar"

export interface UploadItemData {
  filename: string
  jobId: string
  sizeBytes: number
  status: "uploading" | "pending" | "running" | "done"
    | "failed" | "cancelled" | "error"
  progress?: { phase: string; current: number; total: number;
                percent: number; message: string }
  error?: string
  originHash?: string
  chunks?: number
  elapsedMs?: number
  createdAt?: number
  finishedAt?: number
}

interface Props {
  item: UploadItemData
  onCancel: (jobId: string) => void
  onDelete: (jobId: string) => void
  onDetail: (jobId: string) => void
}

function _fmtTime(sec?: number): string {
  if (!sec || sec <= 0) return ""
  const d = new Date(sec * 1000)
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const BORDER: Record<string, string> = {
  done: "#7aa2f7",
  failed: "#ef8585", error: "#ef8585",
  running: "#e29e4a", pending: "#e29e4a",
}

export function UploadItem({ item, onCancel, onDelete, onDetail }: Props) {
  const time = _fmtTime(item.finishedAt || item.createdAt)
  const timeLabel = item.finishedAt ? "完成于" : "创建于"
  const isRunning = item.status === "running" || item.status === "pending"
  const isDone = item.status === "done"
  const isFail = item.status === "failed" || item.status === "error"
  const isCancelled = item.status === "cancelled"

  return (
    <div style={{
      display: "grid", gap: 6,
      padding: "8px 10px", borderRadius: 4, fontSize: 12,
      background: "rgba(118,169,255,.04)",
      borderLeft: "2px solid " + (BORDER[item.status] ?? "transparent"),
    }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <span style={{ flex: 1, minWidth: 0, overflow: "hidden",
                        textOverflow: "ellipsis", whiteSpace: "nowrap",
                        fontSize: 13 }}>
          {item.filename}
        </span>
        {isDone && (
          <>
            <Badge tone="success">成功</Badge>
            <span style={{ opacity: 0.7 }}>
              {item.chunks ?? 0} chunks · {((item.elapsedMs ?? 0) / 1000).toFixed(1)}s
            </span>
          </>
        )}
        {isFail && <Badge tone="danger">失败</Badge>}
        {isCancelled && <Badge tone="muted">已取消</Badge>}
        <span style={{ opacity: 0.5, fontSize: 11 }}>{timeLabel} {time}</span>
        <button className="ind-btn" style={{ fontSize: 11, padding: "2px 8px" }}
          onClick={() => onDetail(item.jobId)}>详情</button>
        {isRunning && (
          <button className="ind-btn" style={{ fontSize: 11, padding: "2px 8px" }}
            onClick={() => onCancel(item.jobId)}>取消</button>
        )}
        {(isDone || isFail || isCancelled) && (
          <button className="ind-btn" style={{ fontSize: 11, padding: "2px 8px" }}
            onClick={() => onDelete(item.jobId)}>删除</button>
        )}
        {isDone && item.originHash && (
          <a href={originUrl(item.originHash)} target="_blank" rel="noreferrer"
            style={{ fontSize: 11, color: "#7aa2f7", textDecoration: "underline" }}>
            原件
          </a>
        )}
      </div>

      {isRunning && (
        <JobProgressBar
          status={item.status}
          phase={item.progress?.phase}
          current={item.progress?.current}
          total={item.progress?.total}
          message={item.progress?.message} />
      )}

      {isFail && item.error && (
        <div style={{ color: "#ef8585", fontSize: 11, opacity: 0.9 }}>
          {item.error.slice(0, 200)}
        </div>
      )}
    </div>
  )
}
