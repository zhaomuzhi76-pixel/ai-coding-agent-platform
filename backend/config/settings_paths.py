from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SettingsPaths:
    """
    Application path configuration.

    Responsibility:

        - runtime directory definitions

    Not Responsible:

        - environment loading
        - model settings
        - service initialization
    """

    VERSION = "1.0"


    def __init__(
        self,
        root: Path | None = None,
    ) -> None:

        self.PROJECT_ROOT = (
            root
            or PROJECT_ROOT
        )

        self.BACKEND_DIR = (
            self.PROJECT_ROOT / "backend"
        )

        self.FRONTEND_DIR = (
            self.PROJECT_ROOT / "frontend"
        )

        self.WORKSPACE_DIR = (
            self.PROJECT_ROOT / "workspace"
        )

        self.LOG_DIR = (
            self.PROJECT_ROOT / "logs"
        )

        self.TEMP_DIR = (
            self.PROJECT_ROOT / "temp"
        )

        self.PROMPT_DIR = (
            self.BACKEND_DIR / "prompts"
        )

        self.MEMORY_DIR = (
            self.PROJECT_ROOT / "memory"
        )


    def dump(
        self,
    ) -> dict:

        return {

            "name":
                "SettingsPaths",

            "version":
                self.VERSION,

            "PROJECT_ROOT":
                self.PROJECT_ROOT,

            "WORKSPACE_DIR":
                self.WORKSPACE_DIR,

            "LOG_DIR":
                self.LOG_DIR,

            "MEMORY_DIR":
                self.MEMORY_DIR,

        }



def build_paths() -> dict[str, Path]:

    return SettingsPaths().dump()



__all__ = [
    "SettingsPaths",
    "PROJECT_ROOT",
    "build_paths",
]
