import {
  describe,
  expect,
  it,
} from "vitest"
import {
  ControlPlaneProvider,
  useControlPlaneContext,
} from "../context/control_plane_context"
import {
  ProjectSessionFeatureController,
} from "../../../features/project_session/project_session_feature_controller"
import {
  AgentWorkspaceStore,
} from "../../../features/agent_workspace/agent_workspace_store"
import {
  ProjectSessionAgentWorkspaceBridge,
} from "../../../features/agent_workspace/context/project_session_agent_workspace_bridge"

describe(
  "control plane context",
  () => {
    it("exposes the canonical three owners", () => {
      expect(
        ControlPlaneProvider,
      ).toBeTypeOf("function")

      expect(
        useControlPlaneContext,
      ).toBeTypeOf("function")

      expect(
        ProjectSessionFeatureController,
      ).toBeTypeOf("function")

      expect(
        AgentWorkspaceStore,
      ).toBeTypeOf("function")

      expect(
        ProjectSessionAgentWorkspaceBridge,
      ).toBeTypeOf("function")
    })
  },
)
