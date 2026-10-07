/**
 * 答案字段兼容层（单一职责）。
 *
 * 背景：
 *   · agent_loop 路径：result.data.answer
 *   · shortcut 路径：  result.data.text
 *   · 历史/兼容：       result.data.message
 *
 * 契约：
 *   pickAnswer(data) → string  （永远返回字符串，空则返回 ""）
 *   explainAnswer(data) → { key, value }  调试用
 */

const CANDIDATES = ["answer", "text", "message", "content", "result"];

export function pickAnswer(data) {
  if (!data || typeof data !== "object") return "";
  for (const k of CANDIDATES) {
    const v = data[k];
    if (typeof v === "string" && v.trim()) return v;
  }
  return "";
}

export function explainAnswer(data) {
  if (!data || typeof data !== "object") return { key: "", value: "" };
  for (const k of CANDIDATES) {
    const v = data[k];
    if (typeof v === "string" && v.trim()) return { key: k, value: v };
  }
  return { key: "", value: "" };
}

export function listCandidateKeys() {
  return [...CANDIDATES];
}
