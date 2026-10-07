import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react"

import { useI18n } from "../../../core/i18n/i18n"
import type { PlatformController } from "../platform_controller"
import { PlatformWsClient, type PlatformWsEvent } from "../ws_client"

import { PlatformKpiRow } from "./platform_kpi_row"
import { PlatformPipelineSteps } from "./platform_pipeline_steps"
import {
  PlatformDomainPicker,
  PlatformModelPicker,
} from "./platform_picker"
import { PlatformProposalCard } from "./platform_proposal_card"
import { PlatformProposalDetail } from "./platform_proposal_detail"
import { PlatformTaskComposer } from "./platform_task_composer"
import { WorkspaceInput } from "./workspace_input"
import { LiveLogPanel, type LiveEvent } from "./live_log_panel"

import "./platform_workbench.css"

export interface PlatformWorkbenchProps {
  controller: PlatformController
  defaultWorkspace: string
  userId: string
  locale: string
}

import { renderPlatformWorkbench } from "./_platform_workbench_parts/render";

export function PlatformWorkbench(props: PlatformWorkbenchProps) {
  const { controller } = props
  const { t } = useI18n()
  const store = controller.store
  const state = useSyncExternalStore(
    store.subscribe.bind(store),
    store.getSnapshot.bind(store),
    store.getSnapshot.bind(store),
  )

  const [workspace, setWorkspace] = useState(props.defaultWorkspace)
  const [wsEvents, setWsEvents] = useState<LiveEvent[]>([])
  const [streaming, setStreaming] = useState(false)
  const wsRef = useRef<PlatformWsClient | null>(null)

  useEffect(() => {
    void controller.init()
  }, [controller])

  // WS 生命周期
  useEffect(() => {
    const client = new PlatformWsClient()
    wsRef.current = client
    const unsub = client.subscribe((evt: PlatformWsEvent) => {
      setWsEvents((prev) => [...prev.slice(-300), evt as LiveEvent])
      if (evt.event === "done") {
        setStreaming(false)
        // 后端 proposal 已生成，注入 store
        if (evt.proposal_id) {
          controller.ingestProposal({
            proposal_id: String(evt.proposal_id),
            task: String(evt.task ?? ""),
            plan: String(evt.plan ?? ""),
            changes: (evt.changes as any[]) ?? [],
            status: String(evt.status ?? "pending"),
          })
        }
      } else if (evt.event === "error") {
        setStreaming(false)
      }
    })
    client.connect().catch(() => {
      // 静默：回退到 REST
    })
    return () => {
      unsub()
      client.close()
    }
  }, [controller])

  const handleWorkspaceChange = (v: string) => {
    setWorkspace(v)
    try {
      localStorage.setItem("biancheng.platform.workspace", v)
    } catch {
      // ignore
    }
  }

  const onProposeViaWs = useCallback(
    async (task: string, files: string[]) => {
      const s = state.session
      if (!s) return
      const client = wsRef.current
      if (!client || !client.ready()) {
        // 回退 REST
        void controller.propose({ task, files })
        return
      }
      setStreaming(true)
      setWsEvents([])
      try {
        client.send({
          action: "propose",
          session_id: s.session_id,
          task,
          files,
          workspace: s.workspace,
          model: state.selectedModel || s.model,
        })
      } catch {
        setStreaming(false)
        void controller.propose({ task, files })
      }
    },
    [state.session, state.selectedModel, controller],
  )

  const active = state.proposals.find(
    (p) => p.proposal_id === state.activeProposalId,
  ) ?? null
  const working = state.phase === "working" || streaming
  const hasSession = Boolean(state.session)

  return renderPlatformWorkbench({ active, controller, handleWorkspaceChange, hasSession, onProposeViaWs, state, t, working, workspace, wsEvents });
}
