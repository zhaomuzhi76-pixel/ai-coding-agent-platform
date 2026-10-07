export type TimeRange = "today" | "7d" | "30d" | "all"

const LABELS: Record<TimeRange, string> = {
  today: "今日",
  "7d": "近 7 天",
  "30d": "近 30 天",
  all: "全部",
}

export function TimeSelector(props: {
  value: TimeRange
  onChange: (v: TimeRange) => void
}) {
  return (
    <div style={{
      display: "inline-flex", gap: 4,
      padding: 2, borderRadius: 6,
      background: "var(--panel-2)",
      border: "1px solid var(--line)",
    }}>
      {(Object.keys(LABELS) as TimeRange[]).map((k) => (
        <button
          key={k}
          onClick={() => props.onChange(k)}
          style={{
            padding: "4px 10px",
            fontSize: 11,
            borderRadius: 4,
            border: "none",
            cursor: "pointer",
            background: props.value === k
              ? "var(--accent)" : "transparent",
            color: props.value === k
              ? "#04101e" : "var(--text-soft)",
            fontFamily: "inherit",
          }}
        >
          {LABELS[k]}
        </button>
      ))}
    </div>
  )
}

export function rangeToDays(r: TimeRange): number | undefined {
  if (r === "today") return 1
  if (r === "7d") return 7
  if (r === "30d") return 30
  return undefined
}

export const TIME_LABELS = LABELS
