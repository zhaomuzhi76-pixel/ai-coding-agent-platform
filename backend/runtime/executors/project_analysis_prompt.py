from __future__ import annotations

from pathlib import Path
from typing import Any


class ProjectAnalysisPrompt:
    """构建"项目分析"提示词。"""

    VERSION = "1.0"

    def build(
        self,
        *,
        workspace: Path,
        task: str,
        wiki: dict[str, str],
        samples: list[dict[str, str]],
    ) -> str:
        parts: list[str] = []
        parts.append(f"# 用户请求\n{task}\n")
        parts.append(f"# 工作区\n`{workspace}`\n")

        for key, label in (
            ("architecture", "架构概要"),
            ("modules", "模块关系"),
            ("conventions", "编码规范"),
        ):
            if wiki.get(key):
                parts.append(
                    f"# {label}（RepoWiki）\n{wiki[key]}\n"
                )

        if samples:
            parts.append(f"# 关键文件样本（{len(samples)} 个）\n")
            for s in samples:
                parts.append(
                    f"## {s['path']}\n```\n{s['content']}\n```\n"
                )

        parts.append(self._task_block())
        return "\n".join(parts)

    @staticmethod
    def _task_block() -> str:
        return (
            "# 任务\n"
            "生成一份 Markdown 报告，必须包含以下 5 个章节（用二级标题）：\n\n"
            "## 1. 项目任务理解\n"
            "这个项目在完成什么任务？解决什么问题？目标用户是谁？"
            "用 3-5 句话说明。\n\n"
            "## 2. 技术栈\n"
            "列出语言、框架、主要依赖。\n\n"
            "## 3. 设计优势\n"
            "至少 3 条。从架构、模块化、命名、可测试性、可扩展性等角度分析。"
            "每条必须引用具体文件或模块作为证据。\n\n"
            "## 4. 设计短板\n"
            "至少 3 条。从耦合、重复、抽象泄漏、缺少测试、文档不足、"
            "错误处理不一致等角度分析。每条必须引用具体证据。\n\n"
            "## 5. 改进建议\n"
            "按优先级排序，每条包含：问题 → 建议 → 影响。\n\n"
            "输出纯 Markdown，不加外层代码块。用中文。"
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["ProjectAnalysisPrompt"]
