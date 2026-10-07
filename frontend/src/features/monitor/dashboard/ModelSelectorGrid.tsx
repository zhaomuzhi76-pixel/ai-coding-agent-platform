/** 模型多选卡片网格 */
import type { TestableModel } from "../../../core/api/benchmark_api"

export function fmtScore(v: number): string {
  const n = v > 1 ? v : v * 100
  return n.toFixed(0)
}

interface Props {
  models: TestableModel[]
  selectedKeys: Set<string>
  toggleModel: (k: string) => void
}

export function ModelSelectorGrid({ models, selectedKeys, toggleModel }: Props) {
  return (
    <div className="bm-block">
      <div className="bm-block-title">选择测试模型（{models.length}）</div>
      <div className="bm-model-grid">
        {models.map((m) => {
          const k = `${m.provider}::${m.model}`
          const sel = selectedKeys.has(k)
          return (
            <div key={k} className={"bm-model-card" + (sel ? " sel" : "")}
                 onClick={() => toggleModel(k)}>
              <div className={"bm-checkbox" + (sel ? " on" : "")}>
                {sel ? "✓" : ""}
              </div>
              <div className="bm-model-info">
                <div className="bm-model-name">{m.display_name || m.model}</div>
                <div className="bm-model-meta">
                  <span>{m.provider}</span>
                  {m.is_local && <span className="bm-tag">本地</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ModelSelectorGrid
