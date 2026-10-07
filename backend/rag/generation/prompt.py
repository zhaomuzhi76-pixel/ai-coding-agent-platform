"""强约束 Prompt 模板（零幻觉）"""

SYSTEM_PROMPT = """你是严格的知识库问答助手。规则：

1. 只能使用【知识库上下文】中的内容，禁止使用外部知识。
2. 每条结论必须带引用标记 [1] [2] 对应上下文序号。
3. 上下文中无相关信息，**必须**原样回复："暂无对应资料"。
4. 禁止推理延伸、参数估算、主观解读。
5. 数值/步骤/工艺参数必须原样引用。

【知识库上下文】
{context}

【用户问题】
{question}

严格按规则回答："""

REFUSAL_TEXT = "暂无对应资料"


def build_prompt(context: str, question: str) -> str:
    return SYSTEM_PROMPT.format(context=context, question=question)


def format_context(hits: list) -> str:
    """把检索结果格式化为带序号的上下文"""
    lines = []
    for i, h in enumerate(hits, 1):
        text = (h.get("text") or "").strip()
        src = h.get("source") or h.get("doc_title") or ""
        page = h.get("page") or h.get("page_no") or 0
        head = f"[{i}] {src}" + (f" p.{page}" if page else "")
        lines.append(f"{head}\n{text}")
    return "\n\n".join(lines)


__all__ = ["SYSTEM_PROMPT", "REFUSAL_TEXT", "build_prompt", "format_context"]
