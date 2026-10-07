from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.config.settings_paths import SettingsPaths


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Global application configuration.

    Responsibility:
        - environment loading
        - application configuration
        - provider/model configuration
        - runtime switches
        - logging configuration
        - filesystem locations

    Not Responsible:
        - service initialization
        - storage logic
        - business logic
    """

    VERSION: ClassVar[str] = "3.1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "BianCheng AI Agent Pro"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    API_PREFIX: str = "/api"

    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = "change-this-secret"


    TEMPERATURE: float = 0.2
    TOP_P: float = 0.95
    MAX_TOKENS: int = 8192



    ENABLE_MEMORY: bool = True
    ENABLE_TOOL_CALLING: bool = True
    ENABLE_REFLECTION: bool = True

    MAX_AGENT_STEPS: int = 30
    SHELL_TIMEOUT: int = 600

    WORKSPACE_DIR: Path = PROJECT_ROOT
    LOG_DIR: Path = PROJECT_ROOT / "logs"
    TEMP_DIR: Path = PROJECT_ROOT / "temp"
    MEMORY_DIR: Path = PROJECT_ROOT / "memory"

    paths: ClassVar[SettingsPaths] = SettingsPaths()

    def create_directories(self) -> None:
        for directory in (
            self.WORKSPACE_DIR,
            self.LOG_DIR,
            self.TEMP_DIR,
            self.MEMORY_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def dump(self) -> dict:
        return {
            "name": "Settings",
            "version": self.VERSION,
            "app": self.APP_NAME,
            "log_level": self.LOG_LEVEL,
            "workspace": str(self.WORKSPACE_DIR),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    config = Settings()
    config.create_directories()
    return config


settings = get_settings()

__all__ = [
    "Settings",
    "settings",
    "get_settings",
]
