"""API 契约定义（框架无关，前端类型由此生成）"""
from typing import Any, Dict

CONTRACT_VERSION = "1.3.0"
BASE_PATH = "/api/model-registry"

ENDPOINTS: Dict[str, Dict[str, str]] = {
    "listProviders":   {"method": "GET",  "path": f"{BASE_PATH}/providers"},
    "createProvider":  {"method": "POST", "path": f"{BASE_PATH}/providers"},
    "listModels":      {"method": "GET",  "path": f"{BASE_PATH}/providers/{{id}}/models"},
    "testProvider":    {"method": "POST", "path": f"{BASE_PATH}/providers/{{id}}/test"},
    "listRoles":       {"method": "GET",  "path": f"{BASE_PATH}/roles"},
    "bindRole":        {"method": "POST", "path": f"{BASE_PATH}/roles"},
    "getKPI":          {"method": "GET",  "path": f"{BASE_PATH}/kpi"},
    "listAllModels":   {"method": "GET",  "path": f"{BASE_PATH}/models"},
    "updateProvider":  {"method": "PATCH", "path": f"{BASE_PATH}/providers/{{id}}"},
    "deleteProvider":  {"method": "DELETE", "path": f"{BASE_PATH}/providers/{{id}}"},
    "usageKPI":        {"method": "GET",  "path": f"{BASE_PATH}/kpi/usage"},
    "exportConfig":    {"method": "GET",  "path": f"{BASE_PATH}/config/export"},
    "exportYAML":      {"method": "GET",  "path": f"{BASE_PATH}/config/export/yaml"},
    "importConfig":    {"method": "POST", "path": f"{BASE_PATH}/config/import"},
    "verifyProvider":  {"method": "POST", "path": f"{BASE_PATH}/providers/{{id}}/verify"},
    "verifiedModels":  {"method": "GET",  "path": f"{BASE_PATH}/verified-models"},
    "providerKinds":   {"method": "GET",  "path": f"{BASE_PATH}/provider-kinds"},
}

TYPES: Dict[str, Dict[str, str]] = {
    "ProviderCard": {
        "id": "string", "name": "string", "kind": "local|cloud",
        "base_url": "string", "has_key": "boolean",
        "enabled": "boolean", "connected": "boolean",
        "model_count": "number",
    },
    "ModelCard": {
        "id": "string", "display": "string", "provider": "string",
        "ctx": "number", "cost_per_1k": "number", "tags": "string[]",
    },
    "RoleCandidate": {"value": "string", "label": "string", "group": "string"},
    "RoleCard": {
        "role": "string", "label": "string", "primary": "string",
        "primary_provider": "string", "fallback": "string|null",
        "ui": "select", "candidates": "RoleCandidate[]",
    },
    "ProviderKindSpec": {
        "value": "string", "label": "string", "category": "local|cloud",
        "default_base_url": "string", "needs_key": "boolean",
        "protocol": "string"},
    "VerifiedModel": {"id": "string", "provider": "string",
                     "display_name": "string", "label": "string"},
    "RegistryKPI": {
        "providers_total": "number", "providers_connected": "number",
        "models_total": "number", "roles_routed": "number",
    },
}


def build_schema() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": CONTRACT_VERSION,
        "basePath": BASE_PATH,
        "endpoints": ENDPOINTS,
        "types": TYPES,
    }
