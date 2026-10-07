"""GitignoreParser: 解析 .gitignore 规则（纯 stdlib）。

支持语法（gitignore 完整子集）：
  - 空行 / # 注释忽略
  - `!pattern` 取反（重新包含）
  - `pattern/` 只匹配目录
  - `/pattern` 锚定根
  - `**/` 任意层级
  - `*` 单段通配
  - `**` 跨段通配
  - 尾部 `/**` 目录内所有

不负责：
  - 读磁盘文件（调用方传文本）
  - 递归目录（只判定单路径）
  - 缓存 / 索引 / 扫描
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class GitignoreRule:
    raw: str
    negated: bool
    dir_only: bool
    anchored: bool
    regex: re.Pattern

    def matches(self, path: str, is_dir: bool) -> bool:
        if self.dir_only and not is_dir:
            return False
        p = path.strip("/")
        if not p:
            return False
        if self.anchored:
            return bool(self.regex.fullmatch(p))
        # 非锚定：任意后缀匹配
        parts = p.split("/")
        for i in range(len(parts)):
            sub = "/".join(parts[i:])
            if self.regex.fullmatch(sub):
                return True
        return False


class GitignoreParser:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._rules: list[GitignoreRule] = []

    def parse(self, text: str) -> None:
        if not isinstance(text, str):
            raise TypeError("text must be str")
        for raw in text.splitlines():
            self._add_rule(raw)

    def load(self, lines: Iterable[str]) -> None:
        for raw in lines:
            self._add_rule(raw)

    def match(self, path: str, is_dir: bool = False) -> bool:
        """返回 True = 被忽略；False = 保留。后者规则覆盖前者（gitignore 语义）。"""
        decision = False
        for rule in self._rules:
            if rule.matches(path, is_dir):
                decision = not rule.negated
        return decision

    def match_verbose(
        self,
        path: str,
        is_dir: bool = False,
    ) -> tuple[bool, bool]:
        """返回 (matched, negated)。

        matched=True 表示至少一条规则命中；
        negated=True 表示"最后命中的规则是取反"（显式重新包含）。

        工业级用途：
          - service 用它判定 "用户是否显式重新包含被 builtin 忽略的项"
          - 单独 match() 只能返回最终 bool，无法区分
            "未命中任何规则" 和 "显式 negation 重新包含"
        """
        matched = False
        last_negated = False
        for rule in self._rules:
            if rule.matches(path, is_dir):
                matched = True
                last_negated = rule.negated
        return matched, last_negated

    def rule_count(self) -> int:
        return len(self._rules)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "rules": self.rule_count(),
            "ready": self.ready(),
        }

    # ── 内部 ──
    def _add_rule(self, raw: str) -> None:
        s = raw.rstrip()
        if not s or s.lstrip().startswith("#"):
            return
        negated = s.startswith("!")
        if negated:
            s = s[1:]
        if not s:
            return
        dir_only = s.endswith("/")
        if dir_only:
            s = s.rstrip("/")
        anchored = s.startswith("/") or "/" in s.rstrip("/")
        if s.startswith("/"):
            s = s[1:]
        if not s:
            return
        regex = self._to_regex(s)
        self._rules.append(GitignoreRule(
            raw=raw, negated=negated, dir_only=dir_only,
            anchored=anchored, regex=regex,
        ))

    @staticmethod
    def _to_regex(pattern: str) -> re.Pattern:
        # 转义普通字符，处理 * ? **
        i, n = 0, len(pattern)
        out: list[str] = []
        while i < n:
            c = pattern[i]
            if c == "*":
                if i + 1 < n and pattern[i + 1] == "*":
                    # ** 跨段
                    out.append(".*")
                    i += 2
                    if i < n and pattern[i] == "/":
                        i += 1
                else:
                    # * 单段
                    out.append("[^/]*")
                    i += 1
            elif c == "?":
                out.append("[^/]")
                i += 1
            else:
                out.append(re.escape(c))
                i += 1
        return re.compile("".join(out))


__all__ = ["GitignoreParser", "GitignoreRule"]
