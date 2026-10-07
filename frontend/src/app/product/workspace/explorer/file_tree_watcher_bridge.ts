/**
 * FileTreeWatcherBridge: /ws/tree 事件 → fileTreeStore 刷新。
 *
 * 单一职责：
 *   - 连 /ws/tree（订阅指定 project）
 *   - 收到 tree_changed → debounce 后重扫根目录
 *   - 调 fileTreeStore.setFiles(files)
 *
 * 不负责：
 *   - 文件树渲染（file_tree_view 管）
 *   - 持久化（workspace_persistence_manager 管）
 *   - 事件语义（后端已过滤）
 *
 * 契约：
 *   - start() / stop() 幂等
 *   - 磁盘事件 200ms 合并（防抖）
 *   - stop() 后不再触发刷新
 */

import type { FileTreeStore, FileNode } from "./file_tree_store"
import {
  TreeSocket,
  type TreeSocketState,
} from "../../../../core/websocket/tree_socket"
import { WS_TREE } from "../../../../core/config/paths"

export interface FileTreeWatcherOptions {
  projectId: string
  workspaceRoot: string
  wsBaseUrl: string
  fileTreeStore: FileTreeStore
  rootLoader: () => Promise<FileNode[]>
  onStateChange?: (state: TreeSocketState) => void
  onError?: (reason: string) => void
}

const DEBOUNCE_MS = 200

export class FileTreeWatcherBridge {
  private socket: TreeSocket | null = null
  private debounceTimer: number | null = null
  private running = false

  private readonly options: FileTreeWatcherOptions

  constructor(options: FileTreeWatcherOptions) {
    this.options = options
  }

  start(): void {
    if (this.running) return
    this.running = true

    const url = this.buildUrl(this.options.wsBaseUrl)
    this.socket = new TreeSocket(url, {
      onReady: () => {
        this.socket?.subscribe(
          this.options.projectId,
          this.options.workspaceRoot,
        )
      },
      onTreeChanged: () => {
        this.scheduleReload()
      },
      onError: (r) => {
        this.options.onError?.(r)
      },
      onStateChange: (s) => {
        this.options.onStateChange?.(s)
      },
    })
    this.socket.connect()
  }

  stop(): void {
    this.running = false
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = null
    }
    if (this.socket) {
      this.socket.unsubscribe()
      this.socket.close()
      this.socket = null
    }
  }

  isRunning(): boolean {
    return this.running
  }

  private scheduleReload(): void {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer)
    }
    this.debounceTimer = window.setTimeout(() => {
      this.debounceTimer = null
      void this.reload()
    }, DEBOUNCE_MS)
  }

  private async reload(): Promise<void> {
    if (!this.running) return
    try {
      const files = await this.options.rootLoader()
      this.options.fileTreeStore.setFiles(files)
    } catch (e) {
      this.options.onError?.(String(e))
    }
  }

  private buildUrl(wsBaseUrl: string): string {
    return wsBaseUrl.replace(/\/ws\/agent\/?$/, WS_TREE)
  }
}

export const FILE_TREE_WATCHER_DEBOUNCE_MS = DEBOUNCE_MS
