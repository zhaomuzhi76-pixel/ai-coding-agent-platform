import { queryIndex, put } from "./indexed_db"

export interface AgentEventRecord {
  id?: number
  sessionId: string
  ts: number
  kind: string
  payload: unknown
}

export interface AgentPatchRecord {
  id?: number
  sessionId: string
  path: string
  before: string
  after: string
  status: "pending" | "accepted" | "rejected" | "failed"
  createdAt: number
  updatedAt: number
  error: string | null
}

export async function appendEvent(
  record: Omit<AgentEventRecord, "id">,
): Promise<void> {
  await put("agent_events", record as AgentEventRecord)
}

export async function listEvents(
  sessionId: string,
): Promise<AgentEventRecord[]> {
  return queryIndex<AgentEventRecord>("agent_events", {
    index: "by_session_ts",
    key: IDBKeyRange.bound(
      [sessionId, 0],
      [sessionId, Number.MAX_SAFE_INTEGER],
    ),
  })
}

export async function savePatch(
  record: Omit<AgentPatchRecord, "id">,
): Promise<number> {
  await put("agent_patches", record as AgentPatchRecord)
  return Date.now()
}

export async function listPatches(
  sessionId: string,
): Promise<AgentPatchRecord[]> {
  return queryIndex<AgentPatchRecord>("agent_patches", {
    index: "by_session_created",
    key: IDBKeyRange.bound(
      [sessionId, 0],
      [sessionId, Number.MAX_SAFE_INTEGER],
    ),
  })
}
