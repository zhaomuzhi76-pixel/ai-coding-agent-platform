import { useState } from "react"
import type { ProjectSessionFeatureController } from "../project_session_feature_controller"

interface ProjectPanelProps {
  controller: ProjectSessionFeatureController
  projectId: string
  setProjectId: (value: string) => void
}

export function ProjectPanel(
  props: ProjectPanelProps,
) {
  const [name, setName] = useState("")
  const [rootPath, setRootPath] = useState("")
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("")

  const project =
    props.controller.store.getSnapshot().project?.project

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
        <span>Project</span>
        <strong>
          {project?.name ?? "No project selected"}
        </strong>
      </header>

      <label>
        Project ID
        <input
          value={props.projectId}
          onChange={event =>
            props.setProjectId(event.target.value)
          }
          placeholder="industrial-project"
        />
      </label>

      <label>
        Name
        <input
          value={name}
          onChange={event =>
            setName(event.target.value)
          }
          placeholder="My AI Project"
        />
      </label>

      <label>
        Root Path
        <input
          value={rootPath}
          onChange={event =>
            setRootPath(event.target.value)
          }
          placeholder="/workspace/project"
        />
      </label>

      <div className="feature-actions">
        <button
          type="button"
          disabled={
            busy || !props.projectId.trim()
          }
          onClick={() =>
            execute(() =>
              props.controller.selectProject(
                props.projectId,
              ),
            )
          }
        >
          Load
        </button>

        <button
          type="button"
          disabled={
            busy
            || !name.trim()
            || !rootPath.trim()
          }
          onClick={() =>
            execute(() =>
              props.controller.createProject({
                project_id:
                  props.projectId.trim() ||
                  undefined,
                name: name.trim(),
                root_path: rootPath.trim(),
              }),
            )
          }
        >
          Create
        </button>
      </div>

      {project && (
        <div className="feature-record">
          <span>{project.project_id}</span>
          <span>{project.root_path}</span>
          <span>
            {project.ready ? "READY" : "NOT READY"}
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
