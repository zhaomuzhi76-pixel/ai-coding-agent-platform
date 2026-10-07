/**
 * WS 结构化日志。
 * Owns: 统一日志格式（事件+代际号+上下文）/ 级别过滤
 * Not:  连接管理 / 重连 / 消息处理
 */

export type LogLevel = "debug" | "info" | "warn" | "error"

export interface LogEntry {
  event: string
  level: LogLevel
  generation?: number
  [key: string]: unknown
}

export class SocketLogger {
  private readonly minLevel: LogLevel

  constructor(minLevel: LogLevel = "info") {
    this.minLevel = minLevel
  }

  private readonly order: Record<LogLevel, number> = {
    debug: 0, info: 1, warn: 2, error: 3,
  }

  log(entry: LogEntry): void {
    if (this.order[entry.level] < this.order[this.minLevel]) return
    const line = `[ws] ${entry.event}`
    switch (entry.level) {
      case "error": console.error(line, entry); break
      case "warn":  console.warn(line, entry);  break
      default:      console.log(line, entry)
    }
  }
}
