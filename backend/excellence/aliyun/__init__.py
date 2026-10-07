"""阿里云-优势子模块：补全 + 单测 + Docstring + 规则审查 + 部署 profile."""
from backend.excellence.aliyun.completion import (
    CompletionContext, Completion, CompletionEngine, prefix_completer,
)
from backend.excellence.aliyun.test_generator import (
    FunctionSpec, TestDraft, TestGenerator,
)
from backend.excellence.aliyun.docstring_writer import (
    DocstringDraft, DocstringWriter,
)
from backend.excellence.aliyun.rule_review import (
    RuleViolation, Rule, ReviewReport, RuleReviewer,
)
from backend.excellence.aliyun.deploy_profile import (
    DeployProfile, DeployProfileBuilder,
)

__all__ = [
    "CompletionContext", "Completion", "CompletionEngine", "prefix_completer",
    "FunctionSpec", "TestDraft", "TestGenerator",
    "DocstringDraft", "DocstringWriter",
    "RuleViolation", "Rule", "ReviewReport", "RuleReviewer",
    "DeployProfile", "DeployProfileBuilder",
]
