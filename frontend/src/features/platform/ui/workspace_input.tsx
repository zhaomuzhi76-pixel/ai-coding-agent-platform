import { useEffect, useState } from "react"

export function WorkspaceInput(props: {
  value: string
  disabled?: boolean
  onChange: (v: string) => void
}) {
  const [draft, setDraft] = useState(props.value)

  useEffect(() => {
    setDraft(props.value)
  }, [props.value])

  return (
    <label
      className="picker"
      style={{ flex: "1 1 260px", minWidth: 200 }}
      title="项目工作区绝对路径"
    >
      <span className="muted">工作区</span>
      <input
        type="text"
        value={draft}
        disabled={props.disabled}
        placeholder="/path/to/project"
        onChange={(e) => {
          setDraft(e.target.value)
          // 实时上抛，无需 Enter/blur
          props.onChange(e.target.value.trim())
        }}
        style={{
          flex: 1,
          border: "none",
          background: "transparent",
          color: "var(--ide-text)",
          fontFamily: "ui-monospace, monospace",
          fontSize: 12,
          outline: "none",
        }}
      />
    </label>
  )
}
