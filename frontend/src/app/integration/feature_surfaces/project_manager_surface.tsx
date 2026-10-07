import {
  useControlPlaneContext,
  useProjectSessionState,
} from "../context/control_plane_context"
import { ProjectManagerView } from "../../../features/project_session/ui/project_manager_view"

export function ProjectManagerSurface() {
  const { projectSession } =
    useControlPlaneContext()
  const state =
    useProjectSessionState()

  return (
    <ProjectManagerView
      projectSession={projectSession}
      state={state}
    />
  )
}
