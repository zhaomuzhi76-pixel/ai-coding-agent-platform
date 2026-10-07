import {
  listDir,
  readFile,
  writeFile,
} from "../../../../core/desktop/desktop_runtime"

import type { FileNode } from "./file_tree_store"
import type { FileNodeSource } from "./file_node_source"

export function createLocalFolderFileSource(
  path: string,
): FileNodeSource {
  return {
    async readText() {
      const res = await readFile(path)
      if (!res) throw new Error(`no desktop runtime: ${path}`)
      return res.content
    },
    async writeText(content: string) {
      const res = await writeFile(path, content)
      if (!res) throw new Error(`no desktop runtime: ${path}`)
    },
  }
}

async function loadLocalChildren(
  dir: string,
): Promise<FileNode[]> {
  const entries = await listDir(dir)
  return entries.map(entry => {
    if (entry.kind === "file") {
      return {
        name: entry.name,
        type: "file" as const,
        source: createLocalFolderFileSource(entry.path),
      }
    }
    return {
      name: entry.name,
      type: "directory" as const,
      loaded: false,
      children: [],
      loadChildren: () => loadLocalChildren(entry.path),
    }
  })
}

function basenameOf(value: string): string {
  const normalized = value.replace(/\\/g, "/")
  const segs = normalized.split("/").filter(Boolean)
  return segs.length > 0 ? segs[segs.length - 1] : value
}

export function createLocalFolderRoot(
  path: string,
): FileNode {
  return {
    name: basenameOf(path),
    type: "directory",
    loaded: false,
    children: [],
    loadChildren: () => loadLocalChildren(path),
  }
}
