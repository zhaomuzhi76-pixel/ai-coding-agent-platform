import { useMemo } from "react"
import { computeDiff, diffStat } from "./diff_lines"
import { useFileTreeVirtual } from "../explorer/use_file_tree_virtual"

interface Props {
  before: string
  after: string
  /** 单行高度（px）。默认 18，与 .diff-review__line 一致。 */
  rowHeight?: number
  /** 视口最大高度（px）。默认 400。 */
  maxHeight?: number
}

const DEFAULT_ROW_HEIGHT = 18
const DEFAULT_MAX_HEIGHT = 400

export function DiffReviewLineView({
  before,
  after,
  rowHeight = DEFAULT_ROW_HEIGHT,
  maxHeight = DEFAULT_MAX_HEIGHT,
}: Props) {
  const lines = useMemo(
    () => computeDiff(before, after),
    [before, after],
  )
  const stat = useMemo(() => diffStat(lines), [lines])

  // 复用现有虚拟滚动 hook（不重复造轮子）
  const { ref, range } = useFileTreeVirtual(lines.length, rowHeight, 12)

  const visible = useMemo(
    () => lines.slice(range.start, range.end),
    [lines, range.start, range.end],
  )

  return (
    <div className="diff-review__lines" data-testid="diff-review-lines">
      <div className="diff-review__lines-stat">
        <span className="add">+{stat.add}</span>
        <span className="del">-{stat.del}</span>
      </div>

      <div
        ref={ref}
        className="diff-review__lines-body"
        style={{ maxHeight, overflow: "auto", position: "relative" }}
      >
        {/* 撑起总高度，让滚动条正确 */}
        <div style={{ height: range.totalHeight, position: "relative" }}>
          <div
            style={{
              position: "absolute",
              top: range.offsetY,
              left: 0,
              right: 0,
            }}
          >
            {visible.map((line, idx) => {
              const absolute = range.start + idx
              return (
                <div
                  key={absolute}
                  className={`diff-review__line diff-review__line--${line.kind}`}
                  style={{ height: rowHeight, lineHeight: `${rowHeight}px` }}
                >
                  <span className="diff-review__gutter">
                    {line.oldNo ?? ""}
                  </span>
                  <span className="diff-review__gutter">
                    {line.newNo ?? ""}
                  </span>
                  <span className="diff-review__mark">
                    {line.kind === "add" ? "+" : line.kind === "del" ? "-" : " "}
                  </span>
                  <span className="diff-review__text">{line.text || " "}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
