/** 调用趋势 —— SVG 折线图（无依赖） */
import type { TrendPoint } from "./api"

interface Props { points: TrendPoint[] }

export function TrendChart({ points }: Props) {
  if (points.length === 0) {
    return <div className="mon-chart mon-empty">暂无数据</div>
  }

  const W = 800, H = 180, PAD = 30
  const maxCalls = Math.max(1, ...points.map(p => p.calls))
  const innerW = W - PAD * 2
  const innerH = H - PAD * 2

  const path = points.map((p, i) => {
    const x = PAD + (i / Math.max(1, points.length - 1)) * innerW
    const y = PAD + innerH - (p.calls / maxCalls) * innerH
    return `${i === 0 ? "M" : "L"}${x},${y}`
  }).join(" ")

  return (
    <div className="mon-chart">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H}>
        <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD}
              stroke="#33333a" />
        <line x1={PAD} y1={PAD} x2={PAD} y2={H - PAD}
              stroke="#33333a" />
        <path d={path} fill="none" stroke="#2563eb" strokeWidth="2" />
        {points.map((p, i) => {
          const x = PAD + (i / Math.max(1, points.length - 1)) * innerW
          const y = PAD + innerH - (p.calls / maxCalls) * innerH
          return <circle key={i} cx={x} cy={y} r="3" fill="#2563eb" />
        })}
      </svg>
      <div className="mon-chart-x">
        {points.filter((_, i) => i % Math.max(1, Math.floor(points.length / 6)) === 0)
          .map((p) => <span key={p.bucket}>{p.bucket.slice(-5)}</span>)}
      </div>
    </div>
  )
}

export default TrendChart
