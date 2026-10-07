/** Agent 意图契约（与后端 agent_entry/intent_router 严格对齐）。
 *
 * 注意：pipeline 层（planner）的 workspace_scan / code_analysis 等
 * 是另一套 Intent 体系（老 pipeline），不在本契约范围内。
 */
export const INTENT = {
  QUERY: "query",
  ANALYZE: "analyze",
  MODIFY: "modify",
  CREATE: "create",
} as const

export type Intent = (typeof INTENT)[keyof typeof INTENT]

export const ALL_INTENTS: readonly Intent[] = [
  INTENT.QUERY,
  INTENT.ANALYZE,
  INTENT.MODIFY,
  INTENT.CREATE,
]
