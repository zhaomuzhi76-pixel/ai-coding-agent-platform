"""Provider 类型注册表：所有支持的厂商 + 默认配置 + 分组"""

PROVIDER_KINDS = [
    {"value": "ollama",    "label": "Ollama",         "category": "local",  "default_base_url": "http://127.0.0.1:11434",  "needs_key": False, "protocol": "ollama"},
    {"value": "vllm",      "label": "vLLM",           "category": "local",  "default_base_url": "http://127.0.0.1:8000/v1", "needs_key": False, "protocol": "openai"},
    {"value": "lmstudio",  "label": "LM Studio",      "category": "local",  "default_base_url": "http://127.0.0.1:1234/v1", "needs_key": False, "protocol": "openai"},
    {"value": "openai",    "label": "OpenAI",         "category": "cloud",  "default_base_url": "https://api.openai.com/v1",       "needs_key": True, "protocol": "openai"},
    {"value": "anthropic", "label": "Anthropic",      "category": "cloud",  "default_base_url": "https://api.anthropic.com/v1",    "needs_key": True, "protocol": "openai"},
    {"value": "dashscope", "label": "阿里云百炼",      "category": "cloud",  "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "needs_key": True, "protocol": "openai"},
    {"value": "deepseek",  "label": "DeepSeek",       "category": "cloud",  "default_base_url": "https://api.deepseek.com/v1",     "needs_key": True, "protocol": "openai"},
    {"value": "zhipu",     "label": "智谱 GLM",        "category": "cloud",  "default_base_url": "https://open.bigmodel.cn/api/paas/v4", "needs_key": True, "protocol": "openai"},
    {"value": "moonshot",  "label": "Moonshot Kimi",  "category": "cloud",  "default_base_url": "https://api.moonshot.cn/v1",      "needs_key": True, "protocol": "openai"},
    {"value": "gemini",    "label": "Google Gemini",  "category": "cloud",  "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "needs_key": True, "protocol": "openai"},
    {"value": "siliconflow","label": "硅基流动",       "category": "cloud",  "default_base_url": "https://api.siliconflow.cn/v1",   "needs_key": True, "protocol": "openai"},
    {"value": "openrouter","label": "OpenRouter",     "category": "cloud",  "default_base_url": "https://openrouter.ai/api/v1",    "needs_key": True, "protocol": "openai"},
    {"value": "custom",    "label": "自定义",          "category": "cloud",  "default_base_url": "",  "needs_key": False, "protocol": "openai"},
]

KIND_MAP = {k["value"]: k for k in PROVIDER_KINDS}


def get_kind(value: str):
    return KIND_MAP.get(value)


def protocol_of(value: str) -> str:
    k = KIND_MAP.get(value)
    return k["protocol"] if k else "openai"
