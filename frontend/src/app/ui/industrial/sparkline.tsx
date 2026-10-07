export function Sparkline(props: {
  values: number[]
  height?: number
}) {
  const values = props.values.length > 0 ? props.values : [0]
  const max = Math.max(...values, 1)
  return (
    <div className="ind-spark" style={{ height: props.height ?? 32 }}>
      {values.map((v, i) => (
        <div
          key={i}
          className="ind-spark__bar"
          style={{ height: `${(v / max) * 100}%` }}
        />
      ))}
    </div>
  )
}
