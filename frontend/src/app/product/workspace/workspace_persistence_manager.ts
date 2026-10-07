import {
  saveWorkspace,
} from "./workspace_persistence_storage"

import type {
  PersistedWorkspace,
} from "./workspace_persistence_contract"

import type {
  FileTreeStore,
} from "./explorer/file_tree_store"

import type {
  WorkspaceStore,
} from "./workspace_store"

import {
  WorkspacePersistenceScheduler,
} from "./workspace_persistence_scheduler"


export class WorkspacePersistence {
  private readonly store: WorkspaceStore
  private readonly fileTree: FileTreeStore

  private resourceKind:
    PersistedWorkspace["kind"] | null = null
  private restoringDepth = 0
  private suspendPersist = 0

  private readonly scheduler =
    new WorkspacePersistenceScheduler()

  private generation = 0


  constructor(
    store: WorkspaceStore,
    fileTree: FileTreeStore,
  ) {
    this.store = store
    this.fileTree = fileTree


    this.store.subscribe(
      () => {
        this.requestPersist()
      },
    )


    this.fileTree.subscribe(
      () => {
        this.requestPersist()
      },
    )
  }


  resetPersistenceQueue(): void {
    this.generation++

    this.scheduler.reset()
  }


  setResourceKind(
    kind: PersistedWorkspace["kind"],
  ): void {
    this.resourceKind = kind
  }
  beginBatch(): void {
    this.suspendPersist++
  }


  endBatch(): void {
    this.suspendPersist =
      Math.max(
        0,
        this.suspendPersist - 1,
      )
  }


  beginRestore(): void {
    this.restoringDepth++
  }


  endRestore(): void {
    this.restoringDepth =
      Math.max(
        0,
        this.restoringDepth - 1,
      )
  }


  private requestPersist(): void {
    if (
      this.restoringDepth > 0
      || this.suspendPersist > 0
    ) {
      return
    }

    this.scheduler.schedule(
      () => this.persistCurrent(),
    )
  }


  async flush(): Promise<void> {
    if (
      this.restoringDepth > 0
      || this.suspendPersist > 0
    ) {
      return
    }

    await this.scheduler.flush(
      () => this.persistCurrent(),
    )
  }


  private async persistCurrent(): Promise<void> {
    const generation =
      this.generation


    const state =
      this.store.getSnapshot()


    if (
      !state.resourceBoundary
      || !state.resourceName
    ) {
      return
    }


    const tree =
      this.fileTree.getSnapshot()


    if (
      generation !== this.generation
    ) {
      console.warn(
        "DROP_STALE_WORKSPACE_SAVE",
      )

      return
    }


    await saveWorkspace(
      {
        version: 1,
        boundary:
          state.resourceBoundary,
        name:
          state.resourceName,        kind:
          this.resourceKind ??
          state.resourceBoundary.targetKind,
        activeFile:
          state.activeFile ?? null,
        expanded:
          [
            ...tree.expanded,
          ]
      },
    )
  }
}
