from __future__ import annotations

from typing import Any


class CapabilityDetector:
    """
    Task capability detector.

    Responsibility:

        - detect required capabilities
        - provide capability evidence

    Not Responsible:

        - task classification
        - complexity estimation
        - risk assessment
        - planning
        - execution
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "capability_detection"
    )

    CAPABILITY_RULES = {
        "code_search": (
            "查找",
            "搜索代码",
            "代码",
            "定位",
            "grep",
            "find",
        ),
        "file_edit": (
            "修改",
            "重构",
            "编辑",
            "替换",
            "修复",
            "modify",
            "change",
            "edit",
            "update",
        ),
        "testing": (
            "测试",
            "错误",
            "bug",
            "验证",
        ),
        "knowledge": (
            "查询",
            "资料",
            "分析",
            "文档",
            "研究",
        ),
        "deployment": (
            "部署",
            "上线",
            "服务器",
            "发布",
        ),
        "workspace_scan": (
            "扫描",
            "目录",
            "项目",
            "文件结构",
            "workspace",
        ),
        "code_analysis": (
            "分析",
            "结构",
            "模块",
            "依赖",
        ),
    }

    def detect(
        self,
        message: str,
    ) -> list[str]:

        return self.detect_detail(
            message
        )["capabilities"]

    def detect_detail(
        self,
        message: str,
    ) -> dict[str, Any]:

        text = (
            message.lower()
            if message
            else ""
        )

        capabilities = []
        matched = []

        for capability, keywords in self.CAPABILITY_RULES.items():

            hits = [
                keyword
                for keyword in keywords
                if keyword.lower() in text
            ]

            if not hits:
                continue

            capabilities.append(
                capability
            )

            matched.append(
                {
                    "capability":
                        capability,

                    "keywords":
                        hits,
                }
            )

        return {
            "capabilities":
                capabilities,

            "matched":
                matched,
        }

    def ready(
        self,
    ) -> bool:

        return bool(
            self.CAPABILITY_RULES
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "CapabilityDetector",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "capability_count":
                len(
                    self.CAPABILITY_RULES
                ),
        }


__all__ = [
    "CapabilityDetector",
]
