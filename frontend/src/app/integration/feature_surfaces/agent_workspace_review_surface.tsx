import {
  useAgentWorkspaceState,
  useControlPlaneContext,
} from "../context/control_plane_context"
import {
  DiffReviewView,
} from "../../product/workspace/diff/diff_review_view"
import type {
  DiffChange,
} from "../../product/workspace/diff/diff_review_contract"
import {
  writeFile,
  readFile,
} from "../../../core/desktop/desktop_runtime"
import {
  localPatchSave,
} from "../../../core/desktop/desktop_local_service"
import {
  projectAgentWorkspaceChanges,
} from "./agent_workspace_changes"
import {
  PendingEditSurface,
} from "../../../features/agent_workspace/events/ui/pending_edit_surface"
import {
  useState,
} from "react"
import {
  useApplyProgress,
} from "../../../features/platform/hooks/use_apply_progress"

function joinPath(root: string, rel: string): string {
  if (!root) return rel
  const r = root.replace(/\/+$/, "")
  const p = rel.replace(/^\/+/, "")
  if (p.startsWith(r + "/") || p === r) return p
  return r + "/" + p
}

export { projectAgentWorkspaceChanges } from "./agent_workspace_changes"

export function AgentWorkspaceReviewSurface() {
  const state = useAgentWorkspaceState()
  const { workspaceController } = useControlPlaneContext()

  const rootPath =
    workspaceController.store.getSnapshot().resourceBoundary?.workspace ?? ""
  const sessionId = state.session?.session_id ?? "anonymous"
  const { progress: applyProg, apply: runApply, reset: resetApply } = useApplyProgress()
  const [pipelinePid, setPipelinePid] = useState("")
  const changes = projectAgentWorkspaceChanges(state.result)

  const onApprove = (approved: readonly DiffChange[]) => {
    void (async () => {
      for (const change of approved) {
        const abs = joinPath(rootPath, change.file)
        try {
          let before = change.before
          try {
            const current = await readFile(abs)
            if (current) before = current.content
          } catch { /* use provided before */ }
          await writeFile(abs, change.after)
          await localPatchSave({
            sessionId, path: abs, before, after: change.after,
            status: "accepted", createdAt: Date.now(),
            updatedAt: Date.now(), error: null,
          })
        } catch (err) {
          await localPatchSave({
            sessionId, path: abs, before: change.before, after: change.after,
            status: "failed", createdAt: Date.now(),
            updatedAt: Date.now(),
            error: err instanceof Error ? err.message : String(err),
          })
        }
      }
      const pid = pipelinePid.trim()
      if (pid) void runApply(pid)
    })()
  }

  const onReject = (rejected: readonly DiffChange[]) => {
    void (async () => {
      for (const change of rejected) {
        await localPatchSave({
          sessionId, path: joinPath(rootPath, change.file),
          before: change.before, after: change.after,
          status: "rejected", createdAt: Date.now(),
          updatedAt: Date.now(), error: null,
        })
      }
    })()
  }

  const onOpenFile = (file: string) => {
    const abs = joinPath(rootPath, file)
    void workspaceController.openFile(abs)
  }

  return (
    <>
      <PendingEditSurface />
      <DiffReviewView
        changes={changes}
        onOpenFile={onOpenFile}
        onApprove={onApprove}
        onReject={onReject}
      />

      <div style={{ marginTop: 12, padding: 12,
                    border: "1px solid #333", borderRadius: 6,
                    background: "rgba(118,169,255,.03)", fontSize: 12 }}>
        <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
          <strong style={{ fontSize: 13 }}>Pipeline Apply</strong>
          <input className="ind-input" style={{ flex: 1, padding: "4px 8px" }}
                 placeholder="proposal_id（选填 · 填后 Approve 会触发审计）"
                 value={pipelinePid}
                 onChange={(e) => setPipelinePid(e.target.value)} />
          <button className="ind-btn-sm"
                  disabled={!pipelinePid.trim() || applyProg.phase === "running"}
                  onClick={() => void runApply(pipelinePid.trim())}>应用</button>
          <button className="ind-btn-sm" onClick={resetApply}>重置</button>
        </div>
        {applyProg.phase !== "idle" && (
          <div style={{ fontSize: 11, color: "#888", fontFamily: "monospace" }}>
            phase: <b>{applyProg.phase}</b> · chunks: {applyProg.chunks.length} · logs: {applyProg.logs.length}
            {applyProg.error && <span style={{ color: "#f87171", marginLeft: 8 }}>err: {applyProg.error}</span>}
          </div>
        )}
      </div>
    </>
  )
}
