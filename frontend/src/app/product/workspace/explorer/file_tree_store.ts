import type {
  FileNodeSource,
} from "./file_node_source"

import {
  normalizePath,
  replaceRoots,
  directoryPaths,
  findNode,
} from "./file_tree_store_support"

export interface FileNode {
  name: string
  type:
    | "file"
    | "directory"
  children?: FileNode[]
  source?: FileNodeSource
  loaded?: boolean
  loadChildren?: () => Promise<FileNode[]>
}

export interface FileTreeSnapshot {
  files: FileNode[]
  expanded: Set<string>
}

export class FileTreeStore {
  private state: FileTreeSnapshot = {
    files: [],
    expanded: new Set(),
  }

  private listeners:
    Array<() => void> = []

  getSnapshot(): FileTreeSnapshot {
    return this.state
  }

  subscribe(
    listener: () => void,
  ) {
    this.listeners.push(listener)

    return () => {
      this.listeners =
        this.listeners.filter(
          item => item !== listener,
        )
    }
  }

  setFiles(
    files: FileNode[],
  ) {
    const nextFiles =
      replaceRoots(files)

    const validDirectories =
      directoryPaths(nextFiles)

    this.state = {
      files: nextFiles,
      expanded:
        new Set(
          [...this.state.expanded]
            .map(normalizePath)
            .filter(
              path =>
                validDirectories.has(path),
            ),
        ),
    }

    this.emit()
  }

  async toggleDirectory(
    path: string,
  ) {
    const normalized =
      normalizePath(path)

    // 关键修复：每次都先尝试加载（幂等），再切换 expanded
    const node =
      findNode(
        this.state.files,
        normalized,
      )

    if (
      node &&
      node.type === "directory" &&
      !node.loaded &&
      node.loadChildren
    ) {
      try {
        node.children =
          await node.loadChildren()
        node.loaded = true
      } catch (error) {
        node.children = []
        node.loaded = true
        // eslint-disable-next-line no-console
        console.error(
          "[file-tree] loadChildren failed:",
          normalized,
          error,
        )
      }
    }

    const expanded =
      new Set(this.state.expanded)

    if (expanded.has(normalized)) {
      expanded.delete(normalized)
    } else {
      expanded.add(normalized)
    }

    // 强制刷新 files 引用（浅拷贝即可，子对象原地修改）
    this.state = {
      ...this.state,
      files: [...this.state.files],
      expanded,
    }

    this.emit()
  }

  setExpanded(
    expanded: readonly string[],
  ) {
    this.state = {
      ...this.state,
      expanded:
        new Set(
          expanded.map(
            normalizePath,
          ),
        ),
    }

    this.emit()
  }

  private emit() {
    for (
      const listener
      of this.listeners
    ) {
      listener()
    }
  }
}
