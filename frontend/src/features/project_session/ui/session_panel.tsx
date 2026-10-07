import { useState } from "react"
import type { ProjectSessionFeatureController } from "../project_session_feature_controller"

interface SessionPanelProps {
  controller: ProjectSessionFeatureController
  projectId: string
}

export function SessionPanel(
  props: SessionPanelProps,
) {
  const [sessionId, setSessionId] = useState("")
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("")

  const state =
    props.controller.store.getSnapshot()
  const session = state.session

  async function execute(
    operation: () => Promise<unknown>,
  ) {
    setBusy(true)
    setMessage("Working...")

    try {
      await operation()
      setMessage("Operation completed")
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Operation failed",
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className="feature-panel">
      <header>
        <span>Session</span>
        <strong>
          {session?.session_id ??
            "No session selected"}
        </strong>
      </header>

      <label>
        Session ID
        <input
          value={sessionId}
          onChange={event =>
            setSessionId(event.target.value)
          }
          placeholder="session-001"
        />
      </label>

      <div className="feature-actions">
        <button
          type="button"
          disabled={
            busy || !props.projectId.trim()
          }
          onClick={() =>
            execute(async () => {
              const result =
                await props.controller.createSession({
                  project_id:
                    props.projectId.trim(),
                  session_id:
                    sessionId.trim() || undefined,
                })

              setSessionId(
                result.session_id,
              )
            })
          }
        >
          Create Session
        </button>

        <button
          type="button"
          disabled={
            busy || !sessionId.trim()
          }
          onClick={() =>
            execute(() =>
              props.controller.startSession(
                sessionId,
              ),
            )
          }
        >
          Start
        </button>

        <button
          type="button"
          disabled={
            busy
            || !sessionId.trim()
            || session?.status !== "active"
          }
          onClick={() =>
            execute(() =>
              props.controller.closeSession(
                sessionId,
              ),
            )
          }
        >
          Close
        </button>

        <button
          type="button"
          disabled={
            busy || !sessionId.trim()
          }
          onClick={() =>
            execute(async () => {
              await props.controller.removeSession(
                sessionId,
              )
              setSessionId("")
            })
          }
        >
          Remove
        </button>
      </div>

      {session && (
        <div className="feature-record">
          <span>
            Status: {session.status}
          </span>
          <span>
            Project: {session.project_id}
          </span>
          <span>
            Ready: {String(session.ready)}
          </span>
        </div>
      )}

      {message && (
        <div className="feature-message">
          {message}
        </div>
      )}
    </article>
  )
}
