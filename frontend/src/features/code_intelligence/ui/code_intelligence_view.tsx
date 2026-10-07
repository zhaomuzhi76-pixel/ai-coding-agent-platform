import {
  useMemo,
  useSyncExternalStore,
} from "react"
import {
  CodeIntelligenceFeatureController,
} from "../code_intelligence_feature_controller"
import type {
  CodeIntelligenceRequest,
} from "../../../core/api/code_intelligence_api"
import { CodeIntelligenceForm } from "./code_intelligence_form"
import { CodeIntelligenceResultView } from "./code_intelligence_result"
import "./code_intelligence.css"

export function CodeIntelligenceView() {
  const controller = useMemo(
    () => new CodeIntelligenceFeatureController(),
    [],
  )

  const state = useSyncExternalStore(
    controller.store.subscribe.bind(
      controller.store,
    ),
    () => controller.store.getSnapshot(),
    () => controller.store.getSnapshot(),
  )

  const submit = async (
    request: CodeIntelligenceRequest,
  ) => {
    try {
      await controller.inspect(request)
    } catch {
      // Store owns the failure state.
    }
  }

  return (
    <section className="code-intelligence">
      <header className="code-intelligence-heading">
        <div>
          <span className="eyebrow">
            CODE INTELLIGENCE
          </span>
          <h2>Project Understanding</h2>
          <p>
            Inspect project structure, files,
            context, impact, and index state.
          </p>
        </div>

        <span className="intelligence-state">
          {state.phase}
        </span>
      </header>

      <div className="code-intelligence-grid">
        <CodeIntelligenceForm
          busy={state.phase === "loading"}
          onSubmit={submit}
        />

        <CodeIntelligenceResultView
          result={state.result}
          error={state.error}
        />
      </div>
    </section>
  )
}
