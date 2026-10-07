/**
 * 时间间隔常量（模块化）。
 *
 * 用法：
 *   setInterval(tick, INTERVALS.fast)
 *   setTimeout(revoke, INTERVALS.objectUrlRevoke)
 */
export const INTERVALS = {
  /** 快速刷新（轮询高频数据，如监控面板） */
  fast: 5_000,
  /** 慢速刷新（如后端健康探测） */
  slow: 30_000,
  /** URL.createObjectURL 释放延迟 */
  objectUrlRevoke: 1_000,
  /** 输入防抖默认窗口 */
  debounce: 400,
} as const

export type IntervalKey = keyof typeof INTERVALS
