class CatalogError(RuntimeError):
    """配置中心无法满足请求时抛出。永不静默兜底。"""

class CatalogNotFound(CatalogError):
    pass

class CatalogInvalid(CatalogError):
    pass
