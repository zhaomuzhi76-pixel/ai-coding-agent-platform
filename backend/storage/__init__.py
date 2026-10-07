"""
Storage infrastructure package.

Concrete infrastructure components are explicitly instantiated
by their owning composition layer.
"""

from backend.storage.mongodb_client import MongoDBClient
from backend.storage.mongodb_config import MongoDBConfig
from backend.storage.redis_client import RedisClient
from backend.storage.redis_config import RedisConfig
from backend.storage.vector_backend import get_vector_store
from backend.storage.vector_config import VectorConfig
from backend.storage.vector_store import VectorStore

__all__ = [
    "MongoDBClient",
    "MongoDBConfig",
    "RedisClient",
    "RedisConfig",
    "VectorConfig",
    "VectorStore",
    "get_vector_store",
]
