import { useState } from "react"
import { ProjectPanel } from "./project_panel"
import { SessionPanel } from "./session_panel"

export interface ProjectManagerViewProps {
  projectSession: import(
    "../project_session_feature_controller"
  ).ProjectSessionFeatureController
  state: import(
    "../project_session_feature_state"
  ).ProjectSessionFeatureState
}

export function ProjectManagerView({
  projectSession,
  state,
}: ProjectManagerViewProps) {
  const [projectId, setProjectId] = useState("")

  return (
    <section className="project-manager">
      <div className="project-manager-heading">
        <div>
          <span className="eyebrow">
            PROJECT MANAGER
          </span>
          <h2>Projects & Sessions</h2>
          <p>
            Manage the execution boundary through
            the canonical backend API.
          </p>
        </div>

        <span className="feature-state">
          {state.phase}
        </span>
      </div>

      <div className="project-manager-grid">
        <ProjectPanel
          controller={projectSession}
          projectId={projectId}
          setProjectId={setProjectId}
        />

        <SessionPanel
          controller={projectSession}
          projectId={projectId}
        />
      </div>

      {state.error && (
        <div className="feature-error">
          {state.error}
        </div>
      )}
    </section>
  )
}
