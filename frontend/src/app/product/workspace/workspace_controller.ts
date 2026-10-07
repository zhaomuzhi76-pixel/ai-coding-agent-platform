import {
  createResourceBoundary,
} from "../../../core/resources/resource_boundary"

import type {
  AgentResourceBoundary,
} from "../../../core/resources/resource_boundary"

import type {
  FileNodeSource,
} from "./explorer/file_node_source"

import type {
  FileNode,
} from "./explorer/file_tree_store"

import {
  WorkspaceStore,
} from "./workspace_store"

import {
  FileTreeStore,
} from "./explorer/file_tree_store"

import {
  WorkspacePersistence,
} from "./workspace_persistence"

import {
  findSource,
} from "./workspace_controller_support"

import {
  restoreWorkspace,
} from "./workspace_controller_restoration"

import {
  createProjectWorkspaceRoot,
} from "./explorer/project_workspace_file_source"

import {
  FileTreeWatcherBridge,
} from "./explorer/file_tree_watcher_bridge"

import {
  runtimeConfig,
} from "../../../core/config/runtime"
import { syncWatcherFromBoundaryImpl, stopWatcherImpl } from "./_workspace_controller_parts/watcher"
import { openFileImpl } from "./_workspace_controller_parts/open_file"

export class WorkspaceController {
  readonly store: WorkspaceStore
  readonly fileTreeStore: FileTreeStore

  private readonly persistence: WorkspacePersistence

  private watcherBridge: FileTreeWatcherBridge | null = null

  constructor(
    store?: WorkspaceStore,
    fileTreeStore?: FileTreeStore,
  ) {
    this.store =
      store ?? new WorkspaceStore()

    this.fileTreeStore =
      fileTreeStore ?? new FileTreeStore()

    this.persistence =
      new WorkspacePersistence(
        this.store,
        this.fileTreeStore,
      )

    // 订阅 store：任何入口（openProject / openResource / restore）
    // 改变 resourceBoundary → 同步 watcher（幂等靠 watcherKey）
    this.store.subscribe(() => this.syncWatcherFromBoundary())
  }

  async openProject(
    projectId: string,
    boundary: AgentResourceBoundary,
  ): Promise<void> {

    const root =
      createProjectWorkspaceRoot(
        projectId,
        boundary.targetPath,
      )

    // 走 setResource —— 同时设 resourceName + resourceBoundary，
    // 保证 persistCurrent 能通过 !resourceName 判空后写入 localStorage。
    this.store.setResource(
      boundary,
      boundary.targetPath,
      null,
      null,
    )

    this.fileTreeStore.setFiles(
      [root],
    )

    this.fileTreeStore.setExpanded(
      [],
    )

    queueMicrotask(() => {
      void this.persistence.flush()
    })

  }

  private watcherKey = ""

  syncWatcherFromBoundary(): void {
    return syncWatcherFromBoundaryImpl(this)
  }

  stopWatcher(): void {
    return stopWatcherImpl(this)
  }

  dispose(): void {
    this.stopWatcher()
  }

  async openResource(
    boundary: AgentResourceBoundary,
    name: string,
    root: FileNode | null,
    activeFile: string | null = null,
  ) {
    this.stopWatcher()
    this.persistence.resetPersistenceQueue()
    this.persistence.beginBatch()

    try {

      this.store.setResource(
        boundary,
        name,
        activeFile,
        null,
      )

      this.fileTreeStore.setFiles(
        root ? [root] : [],
      )

      this.fileTreeStore.setExpanded([])

      const activeSource =
        activeFile && root
          ? findSource(
              [root],
              activeFile,
            )
          : null

      this.store.setActiveFileSource(
        activeSource,
      )
    } finally {
      this.persistence.endBatch()
    }

    queueMicrotask(() => {
      void this.persistence.flush()
    })
  }

  async restore(
    boundary: AgentResourceBoundary,
    name: string,
    root: FileNode | null,
    activeFile: string | null,
    expanded: readonly string[],
    activeFileSource: FileNodeSource | null = null,
  ) {
    await restoreWorkspace(
      {
        persistence: this.persistence,
        store: this.store,
        fileTreeStore: this.fileTreeStore,
      },
      {
        boundary,
        name,
        root,
        activeFile,
        activeFileSource,
        expanded,
      },
    )
  }

  setBoundary(
    boundary: AgentResourceBoundary,
  ) {
    this.store.setBoundary(boundary)
  }

  bumpFileVersion() {
    this.store.bumpFileVersion()
  }

  async openFile(
    file: string,
    source?: FileNodeSource,
  ): Promise<void> {
    return openFileImpl(this, file, source)
  }
}
