import type {
  FileNode,
} from "./explorer/file_tree_store"

import type {
  FileNodeSource,
} from "./explorer/file_node_source"

function normalizePath(
  value: string,
): string {
  return value
    .replace(/\\/g, "/")
    .replace(/^\/+|\/+$/g, "")
}

function samePath(
  actual: string,
  target: string,
): boolean {
  const left =
    normalizePath(actual)

  const right =
    normalizePath(target)

  return (
    left === right ||
    left.endsWith(`/${right}`)
  )
}

export function findSource(
  files: readonly FileNode[],
  target: string,
): FileNodeSource | null {
  const wanted =
    normalizePath(target)

  function visit(
    nodes: readonly FileNode[],
    prefix = "",
  ): FileNodeSource | null {
    for (const node of nodes) {
      const path =
        normalizePath(
          prefix
            ? `${prefix}/${node.name}`
            : node.name,
        )

      if (
        node.type === "file" &&
        node.source &&
        samePath(
          path,
          wanted,
        )
      ) {
        return node.source
      }

      if (node.children) {
        const found =
          visit(
            node.children,
            path,
          )

        if (found) {
          return found
        }
      }
    }

    return null
  }

  return visit(files)
}
