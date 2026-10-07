from __future__ import annotations

from typing import Any


class RiskAssessor:
    """
    Task risk assessor.

    Responsibility:

        - evaluate task risk
        - provide risk evidence

    Not Responsible:

        - permission control
        - security policy
        - approval workflow
        - execution
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "risk_assessment"
    )

    RISK_RULES = {
        "high": (
            "删除",
            "清空",
            "生产数据库",
            "线上数据库",
            "生产环境",
            "危险操作",
        ),
        "medium": (
            "修改",
            "重构",
            "迁移",
            "部署",
            "发布",
            "配置",
        ),
    }

    def assess(
        self,
        message: str,
    ) -> str:

        return self.assess_detail(
            message
        )["level"]

    def assess_detail(
        self,
        message: str,
    ) -> dict[str, Any]:

        text = (
            message.lower()
            if message
            else ""
        )

        for level, keywords in self.RISK_RULES.items():

            hits = [
                keyword
                for keyword in keywords
                if keyword.lower() in text
            ]

            if hits:

                return {
                    "level":
                        level,

                    "matched":
                        [
                            {
                                "level":
                                    level,

                                "keywords":
                                    hits,
                            }
                        ],
                }

        return {
            "level":
                "low",

            "matched":
                [],
        }

    def ready(
        self,
    ) -> bool:

        return bool(
            self.RISK_RULES
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "RiskAssessor",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "rule_groups":
                len(
                    self.RISK_RULES
                ),
        }


__all__ = [
    "RiskAssessor",
]
