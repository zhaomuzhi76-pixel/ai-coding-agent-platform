import { useModelCatalog } from "./useModelCatalog";

export function ModelSelector() {
  const { status, models, selected, select } = useModelCatalog();

  if (status === "loading") {
    return (
      <span className="model-selector model-selector--loading">
        加载模型目录…
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="model-selector model-selector--error">
        模型目录不可用
      </span>
    );
  }

  return (
    <select
      className="model-selector"
      value={selected ?? ""}
      onChange={(e) => select(e.target.value)}
    >
      {models.map((m) => (
        <option key={m.id} value={m.id}>
          {m.displayName}
          {m.isDefault ? "（默认）" : ""}
        </option>
      ))}
    </select>
  );
}
