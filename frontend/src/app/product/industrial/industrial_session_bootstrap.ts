/**
 * 工业级 project/session 持久化引导。
 *
 * 契约：
 *   - 先查 localStorage 里是否有匹配当前 root 的 projectId
 *   - 后端验证后复用；不存在则新建
 *   - session 优先复用 active，无则新建
 *   - 结果写回 localStorage（保证下次冷启动能复用）
 *
 * 效果：关浏览器、关服务器、重启机器，下次打开自动恢复上次项目。
 */
import { projectApi } from "../../../core/api/project_api"
import { projectSessionApi } from "../../../core/api/project_session_api"
import { createResourceBoundary } from "../../../core/resources/resource_boundary"
import { writeLocalWorkspace } from "../workspace/workspace_persistence_local_storage"
import { readLocalWorkspace } from "../workspace/workspace_persistence_local_storage"

export interface SessionBootstrapResult {
  projectId: string
  sessionId: string
  reusedProject: boolean
  reusedSession: boolean
}

function normalizePath(p: string): string {
  if (!p) return ""
  return p
    .replace(/\\/g, "/")
    .replace(/\/+$/, "")
    .toLowerCase()
}

async function tryReuseProject(
  root: string,
): Promise<string | null> {
  const persisted = readLocalWorkspace()
  if (!persisted?.boundary?.projectId) return null
  if (
    normalizePath(persisted.boundary.workspace) !==
    normalizePath(root)
  ) {
    return null
  }
  try {
    const resp = await projectApi.get(persisted.boundary.projectId)
    return resp.project.project_id
  } catch {
    return null
  }
}

async function ensureProject(
  root: string,
  name: string,
): Promise<{ id: string; reused: boolean }> {
  const reused = await tryReuseProject(root)
  if (reused) return { id: reused, reused: true }

  try {
    const created = await projectApi.create({
      name,
      root_path: root,
    })
    return { id: created.project.project_id, reused: false }
  } catch (err) {
    // 后端 400 "already registered"：DB 里已有同 root 的 project，
    // 但我们手里没它的 id —— 从 localStorage 兜底复用。
    const persisted = readLocalWorkspace()
    if (persisted?.boundary?.projectId) {
      try {
        const resp = await projectApi.get(
          persisted.boundary.projectId,
        )
        console.warn(
          "[bootstrap] fallback to persisted projectId:",
          resp.project.project_id,
        )
        return { id: resp.project.project_id, reused: true }
      } catch {
        /* fall through */
      }
    }
    throw err
  }
}

async function ensureSession(
  projectId: string,
): Promise<{ id: string; reused: boolean }> {
  try {
    const list = await projectSessionApi.projectSessions(projectId)
    const active = list.sessions.find((s) => s.status === "active")
    if (active) return { id: active.session_id, reused: true }
  } catch {
    /* fall through */
  }
  let created = await projectSessionApi.create({
    project_id: projectId,
  })
  if (created.status !== "active") {
    created = await projectSessionApi.start(created.session_id)
  }
  return { id: created.session_id, reused: false }
}

function persistBinding(
  root: string,
  name: string,
  projectId: string,
): void {
  try {
    const boundary = createResourceBoundary({
      projectId,
      workspace: root,
      targetPath: ".",
      targetKind: "directory",
    })
    writeLocalWorkspace({
      version: 1,
      boundary,
      name,
      kind: "directory",
      activeFile: null,
      expanded: [name],
    })
  } catch (err) {
    console.warn("[bootstrap] persist failed:", err)
  }
}

export async function bootstrapProjectSession(
  root: string,
  name: string,
): Promise<SessionBootstrapResult> {
  const project = await ensureProject(root, name)
  console.log(
    `[session] project ${project.reused ? "reused" : "registered"}:`,
    project.id,
  )

  const session = await ensureSession(project.id)
  console.log(
    `[session] ${session.reused ? "reused" : "started"}:`,
    session.id,
  )

  persistBinding(root, name, project.id)

  return {
    projectId: project.id,
    sessionId: session.id,
    reusedProject: project.reused,
    reusedSession: session.reused,
  }
}
