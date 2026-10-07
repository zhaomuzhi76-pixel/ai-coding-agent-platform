import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react"

import { useI18n } from "../../../../core/i18n/i18n"
import type { PlatformController } from "../../platform_controller"
import { PlatformWsClient, type PlatformWsEvent } from "../../ws_client"

import { PlatformKpiRow } from "../platform_kpi_row"
import { PlatformPipelineSteps } from "../platform_pipeline_steps"
import {
  PlatformDomainPicker,
  PlatformModelPicker,
} from "../platform_picker"
import { PlatformProposalCard } from "../platform_proposal_card"
import { PlatformProposalDetail } from "../platform_proposal_detail"
import { PlatformTaskComposer } from "../platform_task_composer"
import { WorkspaceInput } from "../workspace_input"
import { LiveLogPanel, type LiveEvent } from "../live_log_panel"

import "../platform_workbench.css"

export interface PlatformWorkbenchProps {
  controller: PlatformController
  defaultWorkspace: string
  userId: string
  locale: string
}

// Auto-extracted render function for PlatformWorkbench.
export interface PlatformWorkbenchRenderProps {
  active: any
  controller: any
  handleWorkspaceChange: any
  hasSession: any
  onProposeViaWs: any
  state: any
  t: any
  working: any
  workspace: any
  wsEvents: any
}

export function renderPlatformWorkbench(props: PlatformWorkbenchRenderProps) {
  const { active, controller, handleWorkspaceChange, hasSession, onProposeViaWs, state, t, working, workspace, wsEvents } = props;
  void active;
  return (

      <div className="platform-workbench">
        <div className="platform-workbench__title">
          <h2>{t("platform.title")}</h2>
          <small>{t("platform.subtitle")}</small>
        </div>

        {state.error && (
          <div className="error-banner">
            <span>{state.error}</span>
            <button
              className="btn"
              onClick={() => controller.clearError()}
            >
              关闭
            </button>
          </div>
        )}

        <PlatformKpiRow state={state} />
        <PlatformPipelineSteps cursor={state.stageCursor} />

        <div className="session-bar">
          <WorkspaceInput
            value={workspace}
            disabled={hasSession || working}
            onChange={handleWorkspaceChange}
          />
          <PlatformModelPicker
            models={state.models}
            value={state.selectedModel}
            disabled={working}
            onChange={(m) => controller.setModel(m)}
          />
          <PlatformDomainPicker
            domains={state.domains}
            value={state.selectedDomain}
            disabled={working}
            onChange={(d) => controller.setDomain(d)}
          />
          <div className="session-bar__spacer" />
          {hasSession ? (
            <span className="muted">
              会话 {state.session!.session_id.slice(0, 8)}
            </span>
          ) : (
            <button
              className="btn btn--primary"
              disabled={
                working || !state.selectedModel || !workspace.trim()
              }
              onClick={() =>
                controller.startSession({
                  workspace: workspace.trim(),
                  userId: props.userId,
                  locale: props.locale,
                  model: state.selectedModel,
                })
              }
            >
              新建会话
            </button>
          )}
        </div>

        <div className="proposal-grid">
          <section className="panel">
            <div className="panel__head">
              <span>提案列表</span>
              <span className="muted">{state.proposals.length}</span>
            </div>
            <div className="panel__body">
              {hasSession && (
                <PlatformTaskComposer
                  disabled={working}
                  defaultFiles="calc.py"
                  onSubmit={(task, files) => onProposeViaWs(task, files)}
                />
              )}
              <LiveLogPanel events={wsEvents} />
              <div style={{ marginTop: 14 }}>
                {state.proposals.length === 0 ? (
                  <div className="muted">暂无提案</div>
                ) : (
                  state.proposals.map((p) => (
                    <PlatformProposalCard
                      key={p.proposal_id}
                      proposal={p}
                      active={p.proposal_id === state.activeProposalId}
                      onSelect={(id) =>
                        controller.setActiveProposal(id)
                      }
                    />
                  ))
                )}
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel__head">
              <span>提案详情</span>
              {active && (
                <span className="muted mono">
                  {active.proposal_id}
                </span>
              )}
            </div>
            <div className="panel__body">
              <PlatformProposalDetail proposal={active} />
              {active && (
                <div
                  className="task-composer__actions"
                  style={{ marginTop: 16, flexWrap: "wrap" }}
                >
                  <button
                    className="btn"
                    disabled={working || active.status !== "pending"}
                    onClick={() => void controller.approve()}
                  >
                    批准
                  </button>
                  <button
                    className="btn btn--danger"
                    disabled={working || active.status !== "pending"}
                    onClick={() => void controller.reject("用户拒绝")}
                  >
                    拒绝
                  </button>
                  <button
                    className="btn btn--primary"
                    disabled={working || active.status !== "approved"}
                    onClick={() => void controller.apply()}
                  >
                    应用
                  </button>
                  <button
                    className="btn"
                    disabled={working || active.status !== "applied"}
                    onClick={() => void controller.verify()}
                  >
                    验证
                  </button>
                  <button
                    className="btn"
                    disabled={working || active.status !== "applied"}
                    onClick={() => void controller.learn()}
                  >
                    学习
                  </button>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
  );
}
