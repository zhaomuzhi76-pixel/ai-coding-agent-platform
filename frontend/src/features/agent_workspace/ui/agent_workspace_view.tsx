import "./agent_workspace.css"

import {
  useEffect,
  useRef,
  type FormEvent,
  type KeyboardEvent,
} from "react"


import {
  useExecutionTimeline,
} from "../events/ui/execution_timeline_projection"
import {
  loadBackendModels,
  type BackendModel,
} from "../../../core/models/backend_models_source"

import {
  loadModelPreference,
} from "../persistence/model_preference_local_store"


import type {
  AgentWorkspaceController,
} from "../controllers/agent_workspace_controller"
import { workspaceLabel, modelLabel } from "./agent_workspace_label"
import { AgentWarmupHint } from "./agent_warmup_hint"
import { AgentComposerHeader } from "./agent_composer_header"
import { AgentComposerContext } from "./agent_composer_context"
import { AgentComposerSend } from "./agent_composer_send"
import { useBackendModels } from "./use_agent_workspace_models"
import { useModelWarmupHint } from "./use_agent_workspace_warmup"
import { ProjectRulesPanel } from "./project_rules_panel"

import type {
  AgentWorkspaceState,
} from "../agent_workspace_state"

export interface AgentWorkspaceViewProps {
  controller: AgentWorkspaceController
  state: AgentWorkspaceState
}

export function AgentWorkspaceView(
  {
    controller,
    state,
  }: AgentWorkspaceViewProps,
) {
  const composerRef =
    useRef<HTMLTextAreaElement | null>(null)

  const {
    backendModels,
    onSelectModel,
  } = useBackendModels(state.model.model, controller)

  // 底部 events 计数：与右侧 timeline 保持一致（只算当前任务）
  const _timeline = useExecutionTimeline(state.messages)
  const timelineCount = _timeline.events.length

  const { showModelWarmupHint } = useModelWarmupHint(state.model.model)

  const executing =
    state.phase === "executing"

  const unavailable =
    executing
    || !state.session
    || !state.message.trim()

  const statusLabel =
    executing
      ? "Running"
      : state.error
        ? "Attention"
        : state.session
          ? "Ready"
          : "Waiting for session"

  function execute() {
    if (unavailable) {
      return
    }

    void controller
      .execute()
      .catch(() => undefined)
  }

  function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    execute()
  }

  function keyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (
      event.nativeEvent.isComposing
      || event.key !== "Enter"
      || (!event.metaKey && !event.ctrlKey)
    ) {
      return
    }

    event.preventDefault()
    event.currentTarget.form?.requestSubmit()
  }

  return (
    <form
      className="agent-composer"
      onSubmit={submit}
    >
      {/* 首次加载提示 */}
      <AgentWarmupHint show={showModelWarmupHint} />

      <AgentComposerHeader state={state} statusLabel={statusLabel} />

      <div className="agent-composer__editor">
        <textarea
          ref={composerRef}
          value={state.message}
          onChange={event =>
            controller.setMessage(
              event.target.value,
            )
          }
          onKeyDown={keyDown}
          disabled={executing}
          spellCheck={false}
          aria-label="Agent message"
          placeholder="Describe what the Agent should do..."
        />
      </div>

      <ProjectRulesPanel
        workspace={state.session?.root_path ?? (state.session as any)?.workspace ?? ""}
      />

      <footer className="agent-composer__footer">
        <AgentComposerContext
          state={state}
          backendModels={backendModels}
          executing={executing}
          timelineCount={timelineCount}
          onSelectModel={onSelectModel}
        />
        <AgentComposerSend
          executing={executing}
          unavailable={unavailable}
        />
      </footer>

      {state.error && (
        <div
          role="alert"
          className="agent-composer__error"
        >
          {state.error}
        </div>
      )}
    </form>
  )
}
