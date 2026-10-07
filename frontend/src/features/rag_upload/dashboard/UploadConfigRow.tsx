interface Props {
  kb: string
  ocrLang: string
  busy: boolean
  onChangeKb: (v: string) => void
  onChangeLang: (v: string) => void
}

const KB_OPTIONS = [
  { value: "general", label: "通用" },
  { value: "tcm", label: "中医" },
  { value: "agriculture", label: "农业" },
  { value: "finance", label: "金融" },
]
const OCR_LANGS = [
  { value: "", label: "自动（简体+英文）" },
  { value: "chinese_cht", label: "繁体中文（古籍）" },
  { value: "ch", label: "简体中文" },
  { value: "en", label: "英文" },
  { value: "japan", label: "日文" },
]

export function UploadConfigRow(p: Props) {
  return (
    <div className="ind-toolbar" style={{ marginBottom: 10 }}>
      <label style={{ display: "flex", gap: 6, alignItems: "center",
                      fontSize: 12, color: "var(--text-soft)" }}>
        知识库领域
        <select className="ind-select" value={p.kb} disabled={p.busy}
                style={{ fontSize: 12 }}
                onChange={(e) => p.onChangeKb(e.target.value)}>
          {KB_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </label>
      <label style={{ display: "flex", gap: 6, alignItems: "center",
                      fontSize: 12, color: "var(--text-soft)" }}>
        OCR 语言
        <select className="ind-select" value={p.ocrLang} disabled={p.busy}
                style={{ fontSize: 12 }}
                onChange={(e) => p.onChangeLang(e.target.value)}>
          {OCR_LANGS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </label>
      <span style={{ fontSize: 11, color: "var(--text-soft)", marginLeft: "auto" }}>
        PDF / 图片 / Word / Excel / PPT / HTML / MD / TXT · ≤1GB
      </span>
    </div>
  )
}
export default UploadConfigRow
