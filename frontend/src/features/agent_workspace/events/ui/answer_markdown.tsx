/** 极简 Markdown 渲染器（无依赖）。
 *
 * 支持：标题 / 无序列表 / 有序列表 / 代码块 / 行内代码 / 粗体 / 段落。
 * 不支持：表格 / 图片 / 链接（可用纯文本替代）。
 */
import * as React from "react"
import { useMemo } from "react"

interface Props {
  text: string
}

type Node =
  | { kind: "h"; level: number; text: string }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; items: string[] }
  | { kind: "code"; lang: string; text: string }
  | { kind: "p"; text: string }

function parse(src: string): Node[] {
  const lines = src.replace(/\r\n/g, "\n").split("\n")
  const out: Node[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // 代码块 ```
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim()
      const buf: string[] = []
      i++
      while (i < lines.length && !lines[i].startsWith("```")) {
        buf.push(lines[i])
        i++
      }
      i++ // 跳过结束 ```
      out.push({ kind: "code", lang, text: buf.join("\n") })
      continue
    }

    // 标题 # / ## / ###
    const h = line.match(/^(#{1,4})\s+(.*)$/)
    if (h) {
      out.push({ kind: "h", level: h[1].length, text: h[2] })
      i++
      continue
    }

    // 无序列表 - / * / +
    if (/^\s*[-*+]\s+/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*+]\s+/, ""))
        i++
      }
      out.push({ kind: "ul", items })
      continue
    }

    // 有序列表 1. / 2.
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""))
        i++
      }
      out.push({ kind: "ol", items })
      continue
    }

    // 空行 → 跳过
    if (!line.trim()) {
      i++
      continue
    }

    // 段落（连续非空行）
    const buf: string[] = []
    while (i < lines.length && lines[i].trim() && !isBlockStart(lines[i])) {
      buf.push(lines[i])
      i++
    }
    out.push({ kind: "p", text: buf.join(" ") })
  }

  return out
}

function isBlockStart(line: string): boolean {
  if (line.startsWith("```")) return true
  if (/^#{1,4}\s/.test(line)) return true
  if (/^\s*[-*+]\s+/.test(line)) return true
  if (/^\s*\d+\.\s+/.test(line)) return true
  return false
}

function inline(text: string): (string | React.ReactElement)[] {
  // 处理 `code` 和 **bold**
  const parts: (string | React.ReactElement)[] = []
  const re = /(`[^`]+`|\*\*[^*]+\*\*)/g
  let last = 0
  let m: RegExpExecArray | null
  let key = 0
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index))
    const tok = m[0]
    if (tok.startsWith("`")) {
      parts.push(<code key={key++}>{tok.slice(1, -1)}</code>)
    } else {
      parts.push(<strong key={key++}>{tok.slice(2, -2)}</strong>)
    }
    last = m.index + tok.length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts
}

export function AnswerMarkdown({ text }: Props) {
  const nodes = useMemo(() => parse(text), [text])

  if (!text.trim()) {
    return <div className="answer-markdown answer-markdown--empty">(无回答)</div>
  }

  return (
    <div className="answer-markdown">
      {nodes.map((n, idx) => {
        if (n.kind === "h") {
          const Tag = (`h${Math.min(n.level + 2, 6)}`) as React.ElementType
          return <Tag key={idx}>{inline(n.text)}</Tag>
        }
        if (n.kind === "ul") {
          return (
            <ul key={idx}>
              {n.items.map((it, j) => <li key={j}>{inline(it)}</li>)}
            </ul>
          )
        }
        if (n.kind === "ol") {
          return (
            <ol key={idx}>
              {n.items.map((it, j) => <li key={j}>{inline(it)}</li>)}
            </ol>
          )
        }
        if (n.kind === "code") {
          return (
            <pre key={idx} className="answer-markdown__code">
              <code>{n.text}</code>
            </pre>
          )
        }
        return <p key={idx}>{inline(n.text)}</p>
      })}
    </div>
  )
}
