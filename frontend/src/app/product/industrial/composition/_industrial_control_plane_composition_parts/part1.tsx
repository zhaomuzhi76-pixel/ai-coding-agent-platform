import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react"

import type {
  Locale,
} from "../../../../../core/i18n/locale"

import type {
  AgentResourceBoundary,
} from "../../../../../core/resources/resource_boundary"

import {
  createIdeSurfaceComposition,
} from "../../../../integration/composition/ide_surface_composition"

import {
  IndustrialCodexWorkspace,
} from "../../../../ui/ide/industrial_codex_workspace"

import type {
  AgentWorkspaceState,
} from "../../../../../features/agent_workspace/agent_workspace_state"

import type {
  AgentWorkspaceStore,
} from "../../../../../features/agent_workspace/agent_workspace_store"






import {
  projectAgentWorkspaceChanges,
  matchChangeForFile,
  applyChange,
  rejectChange,
  joinPath,
} from "../../../../integration/feature_surfaces/agent_workspace_changes"

import {
  createLocalFolderFileSource,
} from "../../../workspace/explorer/local_folder_file_source"

import type {
  IndustrialControlPlaneComposition,
  IndustrialControlPlaneWorkspaceProps,
} from './types'

function IndustrialControlPlaneView(
  props: IndustrialControlPlaneWorkspaceProps,
): ReactNode {
  const workspaceSnapshot =
    useSyncExternalStore(
      props.workspaceController.store.subscribe.bind(
        props.workspaceController.store,
      ),
      props.workspaceController.store.getSnapshot.bind(
        props.workspaceController.store,
      ),
      props.workspaceController.store.getSnapshot.bind(
        props.workspaceController.store,
      ),
    )

  const agentState = useSyncExternalStore(
    props.store.subscribe.bind(props.store),
    props.store.getSnapshot.bind(props.store),
    props.store.getSnapshot.bind(props.store),
  )

  const changes = useMemo(
    () => projectAgentWorkspaceChanges(agentState.result),
    [agentState.result],
  )

  // 已处理过的文件（Accept/Reject 过）
  const [processed, setProcessed] = useState<Set<string>>(new Set())

  // result 每次变化（新任务/清空）时重置
  const lastResult = useRef<unknown>(agentState.result)
  useEffect(() => {
    if (lastResult.current !== agentState.result) {
      lastResult.current = agentState.result
      setProcessed(new Set())
    }
  }, [agentState.result])

  const visibleChanges = useMemo(
    () => changes.filter(c => !processed.has(c.file)),
    [changes, processed],
  )

  const pendingChange = useMemo(() => {
    if (visibleChanges.length === 0) return null

    const activeFile = workspaceSnapshot.activeFile
    const matched = matchChangeForFile(visibleChanges, activeFile)
    if (!matched) return null

    const rootPath =
      workspaceSnapshot.resourceBoundary?.workspace ?? ""
    const abs = joinPath(rootPath, matched.file)
    const sessionId =
      agentState.session?.session_id ?? "anonymous"

    return {
      before: matched.before,
      after: matched.after,
      onApprove: () => {
        void (async () => {
          console.log("[onApprove]", abs)
          const ok = await applyChange(abs, matched, sessionId)
          if (ok) {
            try {
              props.workspaceController.bumpFileVersion()
            } catch (e) {
              console.error("[onApprove] bump failed", e)
            }
          }
          setProcessed(prev => {
            const next = new Set(prev)
            next.add(matched.file)
            return next
          })
        })()
      },
      onReject: () => {
        void (async () => {
          console.log("[onReject]", abs)
          await rejectChange(abs, matched, sessionId)
          setProcessed(prev => {
            const next = new Set(prev)
            next.add(matched.file)
            return next
          })
        })()
      },
    }
  }, [
    visibleChanges,
    workspaceSnapshot.activeFile,
    workspaceSnapshot.resourceBoundary?.workspace,
    agentState.session?.session_id,
    props.workspaceController,
  ])

  // 自动打开下一个待处理文件（用户无需手动点文件树）
  useEffect(() => {
    if (visibleChanges.length === 0) return
    if (pendingChange) return

    const rootPath =
      workspaceSnapshot.resourceBoundary?.workspace ?? ""
    if (!rootPath) return

    const target = visibleChanges[0]
    const abs = joinPath(rootPath, target.file)

    console.log("[auto-open] switching editor to:", abs)
    const source = createLocalFolderFileSource(abs)
    void props.workspaceController.openFile(abs, source)
  }, [
    visibleChanges,
    pendingChange,
    workspaceSnapshot.resourceBoundary?.workspace,
    props.workspaceController,
  ])

  return (
    <div className="industrial-agent-layout">
      <IndustrialCodexWorkspace
        surfaces={
          createIdeSurfaceComposition({
            project: "industrial-codex-workspace",
            activeFile: workspaceSnapshot.activeFile,
            activeFileSource:
              workspaceSnapshot.activeFileSource,
            agentSession:
              agentState.session?.session_id ?? null,
            pendingChange,
            fileVersion: workspaceSnapshot.fileVersion ?? 0,
          })
        }
        state={agentState}
        store={props.store}
        controller={props.controller}
        workspace={props.workspaceController}
      />
    </div>
  )
}

export function createIndustrialControlPlaneComposition():
  IndustrialControlPlaneComposition {
  return {
    workspaceId: "industrial-codex-workspace",
    render(props) {
      return <IndustrialControlPlaneView {...props} />
    },
  }
}

export function createIndustrialControlPlaneWorkspace(
  props: IndustrialControlPlaneWorkspaceProps,
): ReactNode {
  return createIndustrialControlPlaneComposition().render(props)
}
