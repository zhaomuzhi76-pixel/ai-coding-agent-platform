import type { PlatformStageId } from "../../../core/contracts/platform"

const STAGES: PlatformStageId[] = [
  { id: "propose", label: "生成提案" },
  { id: "approve", label: "用户审批" },
  { id: "apply", label: "应用修改" },
  { id: "verify", label: "执行验证" },
  { id: "learn", label: "记忆学习" },
]

export function PlatformPipelineSteps(props: { cursor: number }) {
  return (
    <div className="pipeline">
      {STAGES.map((stage, index) => {
        const done = index < props.cursor
        const active = index === props.cursor
        const cls =
          "pipeline__step"
          + (done ? " pipeline__step--done" : "")
          + (active ? " pipeline__step--active" : "")
        return (
          <div key={stage.id} style={{ display: "contents" }}>
            <div className={cls}>
              <span className="pipeline__dot">
                {done ? "✓" : index + 1}
              </span>
              <span>{stage.label}</span>
            </div>
            {index < STAGES.length - 1 && (
              <div className="pipeline__sep" />
            )}
          </div>
        )
      })}
    </div>
  )
}
