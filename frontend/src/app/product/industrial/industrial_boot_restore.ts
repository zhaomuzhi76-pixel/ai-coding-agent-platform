/**
 * 启动时自动恢复上次打开的 workspace + project session。
 *
 * 工业级契约（对齐 Claude Code / Codex / Qwen Code）：
 *   - 刷新页面后不丢上下文
 *   - 恢复失败只 warn，不阻塞启动
 *   - 独立模块，无 React 依赖，可被任意入口调用
 */
import type { WorkspaceController } from "../workspace/workspace_controller"
import type { ProjectSessionFeatureController } from "../../../features/project_session/project_session_feature_controller"
import type { AgentWorkspaceStore } from "../../../features/agent_workspace/agent_workspace_store"

import {
  readLocalWorkspace,
} from "../workspace/workspace_persistence_local_storage"

import {
  restoreIndustrialWorkspace,
} from "./industrial_workspace_restoration"

export interface BootRestoreDeps {
  workspaceController: WorkspaceController
  projectSession: ProjectSessionFeatureController
  agentWorkspace: AgentWorkspaceStore
}

export interface BootRestoreResult {
  restored: boolean
  reason: string
  projectId?: string
  sessionId?: string
}

export async function runIndustrialBootRestore(
  deps: BootRestoreDeps,
): Promise<BootRestoreResult> {
  const persisted = readLocalWorkspace()

  if (!persisted) {
    return { restored: false, reason: "no-persisted-workspace" }
  }

  const projectId = persisted.boundary?.projectId
  if (!projectId) {
    return { restored: false, reason: "no-project-id" }
  }

  // ── 1. 恢复 workspace 视图 ──
  try {
    await restoreIndustrialWorkspace(
      persisted,
      deps.workspaceController,
    )
  } catch (err) {
    console.warn("BOOT_RESTORE_WORKSPACE_FAIL", err)
    return {
      restored: false,
      reason: "workspace-restore-failed",
      projectId,
    }
  }

  // ── 2. 恢复或新建 project session ──
  try {
    await deps.projectSession.selectProject(projectId)
  } catch (err) {
    console.warn("BOOT_RESTORE_PROJECT_FAIL", err)
    return {
      restored: false,
      reason: "project-select-failed",
      projectId,
    }
  }

  try {
    const active =
      await deps.projectSession.restoreActiveSession(projectId)

    if (active?.status === "active" && active.ready) {
      await deps.agentWorkspace.selectSession(active.session_id)
      return {
        restored: true,
        reason: "session-restored",
        projectId,
        sessionId: active.session_id,
      }
    }

    const created =
      await deps.projectSession.createSession({
        project_id: projectId,
      })

    const started =
      await deps.projectSession.startSession(created.session_id)

    if (started.status !== "active" || !started.ready) {
      return {
        restored: false,
        reason: "session-start-failed",
        projectId,
      }
    }

    await deps.agentWorkspace.selectSession(started.session_id)
    return {
      restored: true,
      reason: "session-created",
      projectId,
      sessionId: started.session_id,
    }
  } catch (err) {
    console.warn("BOOT_RESTORE_SESSION_FAIL", err)
    return {
      restored: false,
      reason: "session-restore-failed",
      projectId,
    }
  }
}

