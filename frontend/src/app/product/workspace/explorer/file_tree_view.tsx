/**
 * 文件树视图（虚拟滚动版 · 工业级布局）。
 * 契约：保持 store / onOpenFile / onToggleDirectory 兼容；只渲染可视区行。
 */
import { useMemo, useSyncExternalStore } from "react"

import type { FileNode, FileTreeStore } from "./file_tree_store"
import { flattenTree, type FlatTreeRow } from "./file_tree_flatten"
import { useFileTreeVirtual } from "./use_file_tree_virtual"

const ROW_HEIGHT = 28      // ← 从 24 加到 28
const OVERSCAN = 10        // ← 从 8 加到 10
const INDENT_BASE = 8      // ← 缩进基准
const INDENT_STEP = 14     // ← 每层缩进

interface Props {
  store: FileTreeStore
  activeFile?: string | null
  onOpenFile?: (node: FileNode, path: string) => void
}

interface RowProps {
  row: FlatTreeRow
  activeFile?: string | null
  expanded: ReadonlySet<string>
  onToggleDirectory: (path: string) => void
  onOpenFile?: (node: FileNode, path: string) => void
}

function Row(props: RowProps) {
  const { row, activeFile, expanded } = props
  const isDir = row.node.type === "directory"
  const opened = expanded.has(row.path)
  const active = activeFile === row.path

  const indent = INDENT_BASE + row.level * INDENT_STEP

  if (isDir) {
    return (
      <button
        type="button"
        className="codex-tree-row codex-directory"
        title={row.path}
        style={{ paddingLeft: indent }}
        onClick={() => void props.onToggleDirectory(row.path)}
      >
        <span className="codex-tree-arrow">{opened ? "▼" : "▶"}</span>
        <span className="codex-tree-icon">📁</span>
        <span className="codex-tree-name">{row.node.name}</span>
      </button>
    )
  }

  return (
    <button
      type="button"
      className={"codex-tree-row codex-file" + (active ? " active" : "")}
      title={row.path}
      style={{ paddingLeft: indent + 12 }}
      onClick={() => props.onOpenFile?.(row.node, row.path)}
    >
      <span className="codex-tree-icon">📄</span>
      <span className="codex-tree-name">{row.node.name}</span>
    </button>
  )
}

export function FileTreeView(props: Props) {
  const subscribe = props.store.subscribe.bind(props.store)
  const getSnapshot = props.store.getSnapshot.bind(props.store)
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)

  const rows = useMemo(
    () => flattenTree(snapshot.files, snapshot.expanded),
    [snapshot.files, snapshot.expanded],
  )

  const { ref, range } = useFileTreeVirtual(rows.length, ROW_HEIGHT, OVERSCAN)
  const visible = rows.slice(range.start, range.end)

  return (
    <section
      className="codex-file-tree"
      data-testid="workspace-file-tree"
    >
      <div className="codex-tree-title">文件</div>

      {snapshot.files.length === 0 ? (
        <div
          className="codex-tree-empty"
          data-testid="workspace-file-tree-empty"
        >
          暂无文件
        </div>
      ) : (
        <div
          ref={ref}
          className="codex-tree-scroll"
          data-testid="workspace-file-tree-scroll"
        >
          <div style={{ height: range.totalHeight, position: "relative" }}>
            <div style={{ transform: "translateY(" + range.offsetY + "px)" }}>
              {visible.map(r => (
                <Row
                  key={r.path}
                  row={r}
                  activeFile={props.activeFile}
                  expanded={snapshot.expanded}
                  onToggleDirectory={path => props.store.toggleDirectory(path)}
                  onOpenFile={props.onOpenFile}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
