import type {
  ExecutionResult,
  SessionResponse,
} from "../../core/api/api_types"
import type {
  AgentRuntimeMessage,
} from "../../core/contracts/execution_event"
import type {
  AgentSocketState,
} from "../../core/websocket/agent_socket"
import type {
  ModelSelection,
} from "../../core/contracts/model"
import { OLLAMA_URL } from "../../core/config/runtime"

export type AgentWorkspacePhase =
  | "idle"
  | "loading_session"
  | "ready"
  | "executing"
  | "success"
  | "error"

export interface AgentWorkspaceState {
  phase: AgentWorkspacePhase
  session: SessionResponse | null
  model: ModelSelection
  message: string
  result: ExecutionResult | null
  error: string | null
  socketState: AgentSocketState
  messages: AgentRuntimeMessage[]
  domains: string[]
  revision: number
}

export const initialAgentWorkspaceState:
  AgentWorkspaceState = {
  phase: "idle",
  session: null,
  model: {
    provider: "ollama",
    model: "",
    // model 由 useModelCatalog() 从 /api/providers/catalog 注入，禁止硬编码（HardcodedModelGate 拦截）
    // hardcoded literal removed by one-shot fixer
    base_url: OLLAMA_URL,
    api_key: "",
  },
  message: "",
  result: null,
  error: null,
  socketState: "idle",
  messages: [],
  revision: 0,
  domains: [],
}
