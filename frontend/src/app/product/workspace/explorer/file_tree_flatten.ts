/**
 * 树 → 扁平可见行（虚拟滚动前置）。
 * 契约：仅输出"已展开"的行；纯函数无副作用。
 */
import type { FileNode } from "./file_tree_store"

export interface FlatTreeRow {
  node: FileNode
  path: string
  level: number
}

function normalizePath(value: string): string {
  return value
    .replace(/\\/g, "/")
    .split("/")
    .filter(Boolean)
    .join("/")
}

export function flattenTree(
  files: readonly FileNode[],
  expanded: ReadonlySet<string>,
): FlatTreeRow[] {
  const out: FlatTreeRow[] = []
  const walk = (nodes: readonly FileNode[], prefix: string, level: number) => {
    for (const n of nodes) {
      const path = normalizePath(prefix ? prefix + "/" + n.name : n.name)
      out.push({ node: n, path, level })
      if (
        n.type === "directory"
        && expanded.has(path)
        && n.children
        && n.children.length > 0
      ) {
        walk(n.children, path, level + 1)
      }
    }
  }
  walk(files, "", 0)
  return out
}
