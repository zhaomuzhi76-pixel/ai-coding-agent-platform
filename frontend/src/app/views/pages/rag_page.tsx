/** RAG 知识库页 —— 已替换为工业级 RagDashboard */
import { RagDashboard } from "../../../features/rag_upload/dashboard/RagDashboard"

export function RagPage() {
  return (
    <div style={{ width: "100%", height: "100%" }}>
      <RagDashboard />
    </div>
  )
}

export default RagPage
