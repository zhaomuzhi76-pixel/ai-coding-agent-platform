import "./editor_diff_view.css"
import { useMemo } from "react"
import { computeDiff, diffStat } from "../diff/diff_lines"

interface Props {
  before: string
  after: string
}

export function EditorDiffView({ before, after }: Props) {
  const lines = useMemo(
    () => computeDiff(before, after),
    [before, after],
  )
  const stat = useMemo(() => diffStat(lines), [lines])

  return (
    <div className="editor-diff" data-testid="editor-diff">
      <div className="editor-diff__stat">
        <span className="add">+{stat.add}</span>
        <span className="del">-{stat.del}</span>
      </div>
      <div className="editor-diff__body">
        {lines.map((line, idx) => (
          <div
            key={idx}
            className={`editor-diff__line editor-diff__line--${line.kind}`}
          >
            <span className="editor-diff__gutter">
              {line.oldNo ?? ""}
            </span>
            <span className="editor-diff__gutter">
              {line.newNo ?? ""}
            </span>
            <span className="editor-diff__mark">
              {line.kind === "add" ? "+" : line.kind === "del" ? "-" : " "}
            </span>
            <span className="editor-diff__text">{line.text || " "}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
