/* B1 结构化数据面板 — 可看数据、可操作、可继续精化。
 * 原组件：FinetunePage
 * 职责：KPI 概览 + 任务列表 + 提交表单 + 详情抽屉
 * 待精化：按下方各分区替换为真实 UI。
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function renderFinetunePage(props: any): any {
  const err = props.error ? String(props.error) : null
  const arrays: Array<[string, any[]]> = []
  const others: Array<[string, any]> = []
  const actions: Array<[string, Function]> = []

  for (const k of Object.keys(props).sort()) {
    const v = props[k]
    if (typeof v === "function") {
      if (/^(handle|on|do|submit|cancel|close|refresh|save|delete|load|toggle|set[A-Z])/.test(k)) {
        actions.push([k, v])
      }
      continue
    }
    if (v === undefined) continue
    if (Array.isArray(v)) { arrays.push([k, v]); continue }
    if (v instanceof Set) { arrays.push([k, Array.from(v)]); continue }
    if (v instanceof Map) { arrays.push([k, Array.from(v.entries())]); continue }
    others.push([k, v])
  }

  return (
    <div style={{
      padding: 20,
      background: "#0f1419",
      color: "#cbd5e1",
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: 12,
      minHeight: 200,
    }}>
      {/* ── 头部 ── */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 14, paddingBottom: 10, borderBottom: "1px solid #2b3b51",
      }}>
        <div style={{
          fontSize: 15, fontWeight: 700, color: "#7aa2f7", letterSpacing: 0.6,
        }}>
          📋 微调管理
        </div>
        <div style={{ fontSize: 10, color: "#68778b" }}>
          KPI 概览 + 任务列表 + 提交表单 + 详情抽屉
        </div>
      </div>

      {/* ── 错误 ── */}
      {err && (
        <div style={{
          background: "rgba(239,133,133,.12)",
          border: "1px solid rgba(239,133,133,.4)",
          borderRadius: 6, padding: "8px 12px",
          marginBottom: 14, color: "#ef8585", wordBreak: "break-all",
        }}>
          ⚠️ error: {err}
        </div>
      )}

      {/* ── 状态提示 ── */}
      {props.loading && (
        <div style={{ marginBottom: 12, color: "#7aa2f7" }}>● 加载中…</div>
      )}
      {props.busy && (
        <div style={{ marginBottom: 12, color: "#7aa2f7" }}>● 处理中…</div>
      )}

      {/* ── 数据数组 ── */}
      {arrays.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {arrays.map(([k, arr]) => (
            <div key={k} style={{
              marginBottom: 12, background: "#1a2330",
              border: "1px solid #2b3b51", borderRadius: 6, padding: "10px 12px",
            }}>
              <div style={{
                fontSize: 11, color: "#7aa2f7", marginBottom: 6, fontWeight: 600,
              }}>
                📦 {k} · {arr.length} 项
              </div>
              {arr.length === 0 ? (
                <div style={{ color: "#68778b", padding: "4px 0" }}>(空)</div>
              ) : (
                <div style={{ maxHeight: 240, overflow: "auto" }}>
                  {arr.slice(0, 12).map((item, i) => (
                    <div key={i} style={{
                      padding: "4px 8px", marginBottom: 3,
                      borderLeft: "2px solid #2b3b51",
                      fontSize: 11, color: "#a8b8cd",
                      whiteSpace: "nowrap", overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}>
                      <span style={{ color: "#68778b", marginRight: 8 }}>
                        #{i}
                      </span>
                      {typeof item === "string" || typeof item === "number"
                        ? String(item)
                        : (item?.name || item?.id || item?.job_id || item?.proposal_id
                            || item?.adapter_id || item?.dataset_id || item?.model
                            || item?.provider || JSON.stringify(item).slice(0, 100))}
                    </div>
                  ))}
                  {arr.length > 12 && (
                    <div style={{ color: "#68778b", padding: "4px 0" }}>
                      … 还有 {arr.length - 12} 项
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── 简单状态 ── */}
      {others.filter(([k, v]) =>
        v !== null && v !== undefined && typeof v !== "object" && k !== "t"
      ).length > 0 && (
        <div style={{
          marginBottom: 16, background: "#1a2330",
          border: "1px solid #2b3b51", borderRadius: 6,
          padding: "10px 12px", fontSize: 11,
        }}>
          <div style={{ color: "#7aa2f7", marginBottom: 6, fontWeight: 600 }}>
            📌 状态
          </div>
          {others
            .filter(([k, v]) =>
              v !== null && v !== undefined && typeof v !== "object" && k !== "t"
            )
            .map(([k, v]) => (
              <div key={k} style={{ display: "flex", padding: "2px 0" }}>
                <span style={{ color: "#68778b", width: 200, flexShrink: 0 }}>{k}</span>
                <span style={{ color: "#a8b8cd", wordBreak: "break-all" }}>
                  {String(v).slice(0, 120)}
                </span>
              </div>
            ))}
        </div>
      )}

      {/* ── 对象 ── */}
      {others.filter(([_, v]) => v !== null && typeof v === "object" && !Array.isArray(v)).length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {others
            .filter(([_, v]) => v !== null && typeof v === "object" && !Array.isArray(v))
            .map(([k, v]) => (
              <details key={k} style={{
                marginBottom: 8, background: "#1a2330",
                border: "1px solid #2b3b51", borderRadius: 6, padding: "8px 12px",
              }}>
                <summary style={{
                  cursor: "pointer", color: "#7aa2f7", fontSize: 11,
                }}>
                  🔍 {k} (object)
                </summary>
                <pre style={{
                  fontSize: 10, marginTop: 6, margin: 0,
                  color: "#a8b8cd", whiteSpace: "pre-wrap", wordBreak: "break-all",
                  maxHeight: 200, overflow: "auto",
                }}>
                  {JSON.stringify(v, null, 2).slice(0, 1500)}
                </pre>
              </details>
            ))}
        </div>
      )}

      {/* ── 可触发动作 ── */}
      {actions.length > 0 && (
        <div style={{
          marginTop: 16, paddingTop: 12, borderTop: "1px solid #2b3b51",
        }}>
          <div style={{
            fontSize: 11, color: "#7aa2f7", marginBottom: 8, fontWeight: 600,
          }}>
            🎯 可触发动作 ({actions.length})
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {actions.map(([k, fn]) => (
              <button
                key={k}
                onClick={() => {
                  try { fn() } catch (e) { console.error("action failed:", k, e) }
                }}
                style={{
                  padding: "4px 10px", fontSize: 10,
                  background: "#1a2330", color: "#a8b8cd",
                  border: "1px solid #2b3b51", borderRadius: 4,
                  cursor: "pointer", fontFamily: "inherit",
                }}
                title={"调用 " + k}
              >
                {k.replace(/^(handle|on|do)/, "").replace(/^./, (c) => c.toUpperCase())}
              </button>
            ))}
          </div>
          <div style={{
            fontSize: 9, color: "#5a6b7d", marginTop: 8,
          }}>
            ⓘ 按钮直接调用对应 handler；带参数的动作请人工触发或按 B2 精化。
          </div>
        </div>
      )}

      <div style={{
        marginTop: 16, paddingTop: 8, borderTop: "1px solid #2b3b51",
        fontSize: 9, color: "#5a6b7d",
      }}>
        共 {Object.keys(props).length} 个 props · {arrays.length} 数组 ·
        {others.length} 状态 · {actions.length} 动作
      </div>
    </div>
  )
}
