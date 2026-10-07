/* 从 workspace_controller.ts 抽出：watcher 管理。 */
import { runtimeConfig } from "../../../../core/config/runtime"
import { FileTreeWatcherBridge } from "../explorer/file_tree_watcher_bridge"
import { createProjectWorkspaceRoot } from "../explorer/project_workspace_file_source"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function syncWatcherFromBoundaryImpl(self: any): void {
  const snapshot = self.store.getSnapshot()
  const boundary = snapshot.resourceBoundary
  if (!boundary || boundary.targetKind !== "directory") {
    self.stopWatcher()
    return
  }
  const projectId = String(boundary.projectId || "").trim()
  const workspaceRoot = String(boundary.workspace || "").trim()
  if (!projectId || !workspaceRoot) {
    self.stopWatcher()
    return
  }
  const isAbsolute =
    workspaceRoot.startsWith("/") ||
    /^[A-Za-z]:[\\/]/.test(workspaceRoot)
  if (!isAbsolute) {
    self.stopWatcher()
    return
  }
  const key = projectId + "|" + workspaceRoot
  if (key === self.watcherKey) return
  self.stopWatcher()
  const bridge = new FileTreeWatcherBridge({
    projectId,
    workspaceRoot,
    wsBaseUrl: runtimeConfig.wsBaseUrl,
    fileTreeStore: self.fileTreeStore,
    rootLoader: async () => {
      const root = createProjectWorkspaceRoot(projectId, workspaceRoot)
      if (root.loadChildren) {
        root.children = await root.loadChildren()
        root.loaded = true
      }
      return [root]
    },
    onError: (reason: string) => {
      console.warn("[tree-watcher]", reason)
    },
  })
  bridge.start()
  self.watcherBridge = bridge
  self.watcherKey = key
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function stopWatcherImpl(self: any): void {
  self.watcherKey = ""
  if (self.watcherBridge) {
    self.watcherBridge.stop()
    self.watcherBridge = null
  }
}
