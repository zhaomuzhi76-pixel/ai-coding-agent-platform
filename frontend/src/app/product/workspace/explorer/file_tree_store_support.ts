import type {
  FileNode,
} from "./file_tree_store"

export function normalizePath(
  value: string,
): string {
  return value
    .replace(/\\/g, "/")
    .replace(/^\/+|\/+$/g, "")
}

export function replaceRoots(
  files: readonly FileNode[],
): FileNode[] {
  const seen = new Set<string>()
  const result: FileNode[] = []

  for (const file of files) {
    const key =
      `${file.type}:${normalizePath(file.name)}`

    if (seen.has(key)) {
      continue
    }

    seen.add(key)
    result.push(file)
  }

  return result
}

export function directoryPaths(
  files: readonly FileNode[],
  prefix = "",
): Set<string> {
  const paths = new Set<string>()

  for (const file of files) {
    if (file.type !== "directory") {
      continue
    }

    const path =
      normalizePath(
        prefix
          ? `${prefix}/${file.name}`
          : file.name,
      )

    paths.add(path)

    if (file.children) {
      for (
        const childPath of directoryPaths(
          file.children,
          path,
        )
      ) {
        paths.add(childPath)
      }
    }
  }

  return paths
}

export function findNode(
  nodes: FileNode[],
  target: string,
  prefix = "",
): FileNode | null {
  const wanted = normalizePath(target)

  for (const node of nodes) {
    const current = normalizePath(
      prefix
        ? `${prefix}/${node.name}`
        : node.name,
    )

    if (current === wanted) {
      return node
    }

    if (node.children && node.children.length > 0) {
      const found = findNode(
        node.children,
        wanted,
        current,
      )

      if (found) {
        return found
      }
    }
  }

  return null
}

export function findParentPath(
  target: string,
): string {
  const normalized = normalizePath(target)
  const segments = normalized.split("/")

  if (segments.length <= 1) {
    return ""
  }

  segments.pop()
  return segments.join("/")
}
