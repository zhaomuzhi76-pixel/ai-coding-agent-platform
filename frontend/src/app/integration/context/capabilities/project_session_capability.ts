import type { ProjectSessionFeatureState } from "../../../../features/project_session/project_session_feature_state"

export interface ProjectSessionCapability {

  snapshot(): ProjectSessionFeatureState

  activate(
    project:string
  ):void

}
