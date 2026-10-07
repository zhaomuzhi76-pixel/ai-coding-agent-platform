import { useEditorPreferences } from "./use_editor_preferences"

const PRESET_COLORS = [
  "#d9e2ec", // 默认浅灰白
  "#e8f0fa", // 高对比白
  "#a6d189", // 绿
  "#e5c07b", // 暖黄
  "#e06c75", // 红
  "#c678dd", // 紫
  "#61afef", // 蓝
  "#56b6c2", // 青
]

export function EditorPreferencesControls() {
  const prefs = useEditorPreferences()
  return (
    <div className="editor-prefs" aria-label="Editor preferences">
      <button
        type="button"
        className="editor-prefs__btn"
        onClick={prefs.decreaseFontSize}
        title="减小字号"
      >
        A−
      </button>
      <span className="editor-prefs__value">
        {prefs.preferences.fontSize}px
      </span>
      <button
        type="button"
        className="editor-prefs__btn"
        onClick={prefs.increaseFontSize}
        title="增大字号"
      >
        A+
      </button>

      <span className="editor-prefs__swatches" aria-label="Text color">
        {PRESET_COLORS.map((c) => (
          <button
            key={c}
            type="button"
            className="editor-prefs__swatch"
            style={{ background: c }}
            onClick={() => prefs.setForeground(c)}
            title={c}
            aria-label={`Use color ${c}`}
            data-active={prefs.preferences.foreground === c}
          />
        ))}
      </span>

      <label className="editor-prefs__custom" title="自定义颜色">
        <input
          type="color"
          className="editor-prefs__color"
          value={prefs.preferences.foreground}
          onChange={(e) => prefs.setForeground(e.target.value)}
        />
      </label>

      <button
        type="button"
        className="editor-prefs__btn"
        onClick={prefs.reset}
        title="重置"
      >
        ⟲
      </button>
    </div>
  )
}
