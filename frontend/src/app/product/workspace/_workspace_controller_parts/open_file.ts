/* 从 workspace_controller.ts 抽出：openFile。 */
import {
  createResourceBoundary,
} from "../../../../core/resources/resource_boundary"
import type { FileNodeSource } from "../explorer/file_node_source"
import { findSource } from "../workspace_controller_support"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function openFileImpl(
  self: any,
  file: string,
  source?: FileNodeSource,
): Promise<void> {
  const current = self.store.getSnapshot().resourceBoundary

  if (current) {
    let targetPath = file
    const root = current.workspace ?? ""
    if (root && file.startsWith(root + "/")) {
      targetPath = file.slice(root.length + 1)
    }
    try {
      self.store.setBoundary(
        createResourceBoundary({
          ...current,
          targetPath,
          targetKind: "file",
        }),
      )
    } catch (err) {
      console.error("[openFile] setBoundary failed", err)
    }
  }

  const resolvedSource =
    source ??
    findSource(
      self.fileTreeStore.getSnapshot().files,
      file,
    )

  self.store.selectFile(
    file,
    resolvedSource,
  )
}
