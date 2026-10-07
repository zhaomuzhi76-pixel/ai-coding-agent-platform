import {
  useMemo,
} from "react"
import type {
  AgentRuntimeMessage,
} from "../../../../core/contracts/execution_event"
import {
  ExecutionEventTimeline,
} from "../execution_event_timeline"

/**
 * 定位"当前任务起点"下标。
 *
 * 算法：从 messages 末尾往前扫，找最后一次 step 号回退的位置。
 * agent_loop 每次新任务 step 从 1 重新计数，所以出现
 * 「当前 step 号 > 上一个（更靠后）step 号」→ 说明越过了任务边界。
 *
 * 例：messages = [s=1,s=2,s=3,s=4,s=5, s=1,s=2,s=3]
 * 从末尾扫：3→2→1（正常回退）碰到 5 时 5>1 → 边界在 5 后一位。
 *
 * 找不到边界 → 返回 0（只有一个任务）。
 */
function findCurrentTaskStart(
  messages: readonly AgentRuntimeMessage[],
): number {
  let prevStep = Number.POSITIVE_INFINITY

  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i]
    if (m.type !== "step") continue

    const v2 = m.data as {
      data?: { step?: unknown }
    }
    const stepNo = Number(v2?.data?.step)
    if (!Number.isFinite(stepNo)) continue

    if (stepNo > prevStep) {
      return i + 1
    }
    prevStep = stepNo
  }

  return 0
}

export function useExecutionTimeline(
  messages: readonly AgentRuntimeMessage[],
) {
  return useMemo(() => {
    const timeline = new ExecutionEventTimeline()
    const start = findCurrentTaskStart(messages)
    for (let i = start; i < messages.length; i++) {
      timeline.append(messages[i])
    }
    return timeline.snapshot()
  }, [messages])
}
