"""L4 插件能力声明（纯数据，无副作用）。"""
PLUGIN_DESCRIPTOR = {
    "name": "rag_review_gate",
    "version": "1.0.0",
    "description": "L23 审核门 + 可视化召回（两阶段入库）",
    "capabilities": (
        "draft_review",
        "visual_recall",
        "approval_route",
        "dify_human_input_bridge",
    ),
    "entry": (
        "backend.rag.ingest.review.orchestration.review_plugin:RagReviewPlugin"
    ),
    "layers": ("foundation", "storage", "review", "orchestration", "api"),
}
