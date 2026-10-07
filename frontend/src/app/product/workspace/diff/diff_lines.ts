export type LineKind = "ctx" | "add" | "del"

export interface DiffLine {
  kind: LineKind
  text: string
  oldNo: number | null
  newNo: number | null
}

export function computeDiff(before: string, after: string): DiffLine[] {
  const a = before.split("\n")
  const b = after.split("\n")
  const n = a.length
  const m = b.length
  const dp: number[][] = Array.from(
    { length: n + 1 },
    () => new Array(m + 1).fill(0),
  )
  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = m - 1; j >= 0; j -= 1) {
      dp[i][j] = a[i] === b[j]
        ? dp[i + 1][j + 1] + 1
        : Math.max(dp[i + 1][j], dp[i][j + 1])
    }
  }
  const out: DiffLine[] = []
  let i = 0, j = 0
  let oldNo = 1, newNo = 1
  while (i < n && j < m) {
    if (a[i] === b[j]) {
      out.push({ kind: "ctx", text: a[i], oldNo, newNo })
      i += 1; j += 1; oldNo += 1; newNo += 1
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.push({ kind: "del", text: a[i], oldNo, newNo: null })
      i += 1; oldNo += 1
    } else {
      out.push({ kind: "add", text: b[j], oldNo: null, newNo })
      j += 1; newNo += 1
    }
  }
  while (i < n) {
    out.push({ kind: "del", text: a[i], oldNo, newNo: null })
    i += 1; oldNo += 1
  }
  while (j < m) {
    out.push({ kind: "add", text: b[j], oldNo: null, newNo })
    j += 1; newNo += 1
  }
  return out
}

export function diffStat(lines: DiffLine[]): { add: number; del: number } {
  let add = 0, del = 0
  for (const l of lines) {
    if (l.kind === "add") add += 1
    if (l.kind === "del") del += 1
  }
  return { add, del }
}
