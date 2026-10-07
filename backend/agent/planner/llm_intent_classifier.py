from __future__ import annotations
from backend.config.constants.endpoints import (
    OLLAMA_URL,
)

import json
import os
import re
from typing import Any

import httpx

from backend.agent.planner.intent_classifier_prompt import (
    SUPPORTED_INTENTS,
    build_system_prompt,
)


class LLMIntentClassifier:
    """关键词失败时的 LLM 兜底意图识别。"""

    VERSION = "2.0"
    RESPONSIBILITY = ("llm_intent_classification",)

    SUPPORTED_INTENTS = SUPPORTED_INTENTS

    DEFAULT_BASE_URL = OLLAMA_URL

    EDIT_VERBS = (
        "加", "添加", "增加", "插入", "追加",
        "修改", "改", "编辑", "调整", "更新",
        "删除", "移除", "去掉", "重构", "重写", "替换",
        "add", "insert", "append",
        "modify", "change", "edit", "update",
        "delete", "remove", "refactor", "rewrite", "replace",
    )
    READONLY_HINTS = (
        "分析", "解释", "说明", "讲解",
        "read", "explain", "analyze", "describe", "inspect",
    )

    def __init__(
        self, base_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.call_count = 0
        self.failure_count = 0

    async def classify(
        self, *, message: str, model: str,
    ) -> dict[str, Any]:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("classify message required")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("classify model required")

        self.call_count += 1
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
            ) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system",
                             "content": build_system_prompt()},
                            {"role": "user",
                             "content": f"User message:\n{message}\n\n"
                                        "Classify this message."},
                        ],
                        "stream": False,
                        "format": "json",
                        "temperature": 0.0,
                    },
                )
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("message", {}).get("content", "")
            return self._parse(raw, raw_message=message)
        except Exception:
            self.failure_count += 1
            raise

    def _parse(
        self, raw: str, raw_message: str = "",
    ) -> dict[str, Any]:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("LLM returned empty classification")

        text = raw.strip()
        if text.startswith("```"):
            text = self._strip_fence(text)

        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("LLM classification not valid JSON")
            try:
                value = json.loads(text[start:end + 1])
            except json.JSONDecodeError as error:
                raise ValueError(
                    "LLM classification not valid JSON"
                ) from error

        if not isinstance(value, dict):
            raise ValueError("LLM classification must be object")

        intent = value.get("intent")
        if intent not in self.SUPPORTED_INTENTS:
            intent = "text_generate"

        params = value.get("parameters")
        if not isinstance(params, dict):
            params = {}

        intent = self._keyword_fallback(intent, raw_message)

        return {"intent": intent, "parameters": params}

    @classmethod
    def _keyword_fallback(cls, intent: str, raw_message: str) -> str:
        if not isinstance(raw_message, str) or not raw_message:
            return intent

        UNDERSTAND = (
            "做什么", "干什么", "介绍", "优势", "短板", "优缺点",
            "设计理念", "设计思路", "任务是", "目标是", "用来",
            "整体介绍", "简述",
        )
        if intent in ("code_analysis", "workspace_scan",
                      "understand_project") and any(
            h in raw_message for h in UNDERSTAND
        ):
            print(f"[intent-fallback] {intent!r} → 'understand_project'",
                  flush=True)
            return "understand_project"

        if intent not in ("code_analysis", "understand_project"):
            return intent

        low = raw_message.lower()
        if any(w in low for w in cls.READONLY_HINTS):
            return intent

        hit = next(
            (w for w in cls.EDIT_VERBS if w.lower() in low), None,
        )
        if not hit:
            return intent

        multi = ("所有", "全部", "每个", "批量", "整个项目", "全项目",
                 "all ", "every ", "each file")
        if any(h in low for h in multi):
            print(f"[intent-fallback] {intent!r} → 'edit_multiple_files' "
                  f"(verb={hit!r})", flush=True)
            return "edit_multiple_files"

        print(f"[intent-fallback] {intent!r} → 'file_edit' "
              f"(verb={hit!r})", flush=True)
        return "file_edit"

    @staticmethod
    def _strip_fence(text: str) -> str:
        first = text.find("\n")
        last = text.rfind("```")
        if first < 0 or last <= first:
            return text
        return text[first + 1:last].strip()

    def ready(self) -> bool:
        return bool(self.base_url)

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "call_count": self.call_count,
            "failure_count": self.failure_count,
        }


__all__ = ["LLMIntentClassifier"]
