from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


class EnvironmentLoader:
    VERSION = "1.0"

    def __init__(
        self,
        root: str | Path | None = None,
    ) -> None:
        self.root = (
            Path(root).resolve()
            if root is not None
            else Path.cwd().resolve()
        )
        self.loaded = False

    def load(self) -> bool:
        env_file = self.root / ".env"

        if not env_file.is_file():
            return False

        loaded = load_dotenv(
            env_file,
            override=False,
        )
        self.loaded = bool(loaded)
        return self.loaded

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "root": str(self.root),
            "loaded": self.loaded,
            "ready": self.ready(),
        }


__all__ = ["EnvironmentLoader"]
