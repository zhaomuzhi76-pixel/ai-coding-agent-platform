import {
  getDesktopRuntime,
} from "./desktop_runtime_access"
import type {
  FsEntry,
  FileReadResult,
  FileWriteResult,
  PickedFolder,
} from "./desktop_runtime_contract"

export async function selectFolder(): Promise<PickedFolder | null> {
  const runtime = getDesktopRuntime()
  if (!runtime) return null
  return runtime.selectFolder()
}

export async function allowRoot(root: string): Promise<boolean> {
  const runtime = getDesktopRuntime()
  if (!runtime) return false
  return runtime.allowRoot(root)
}

export async function listDir(dir: string): Promise<FsEntry[]> {
  const runtime = getDesktopRuntime()
  if (!runtime) return []
  return runtime.listDir(dir)
}

export async function readFile(
  path: string,
): Promise<FileReadResult | null> {
  const runtime = getDesktopRuntime()
  if (!runtime) return null
  return runtime.readFile(path)
}

export async function writeFile(
  path: string,
  content: string,
): Promise<FileWriteResult | null> {
  const runtime = getDesktopRuntime()
  if (!runtime) return null
  return runtime.writeFile(path, content)
}
