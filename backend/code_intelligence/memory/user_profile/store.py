"""UserProfileStore facade."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.code_intelligence.memory._shared.singleton import (
    SingletonMixin,
)
from backend.code_intelligence.memory.user_profile.contract import (
    VERSION as _VERSION,
)
from backend.code_intelligence.memory.user_profile.observation_store import (
    distill_preference,
    record_observation,
)
from backend.code_intelligence.memory.user_profile.preference_query import (
    render_context as _render_context,
    top_preferences as _top_preferences,
)
from backend.code_intelligence.memory.user_profile.preference_store import (
    decay_stale as _decay_stale,
    reinforce as _reinforce,
    weaken as _weaken,
)
from backend.code_intelligence.memory.user_profile.schema import init_schema
from backend.code_intelligence.memory.user_profile.stats_view import (
    stats as _stats,
)


class UserProfileStore(SingletonMixin):
    """Cross-project user habit/personalization store."""

    VERSION = _VERSION

    def __init__(self) -> None:
        root = Path.home() / ".biancheng" / "global"
        root.mkdir(parents=True, exist_ok=True)
        self.db_path = root / "global.db"
        init_schema(self.db_path)

    def observe(self, *, workspace: str, category: str,
                signal: str, payload: Dict[str, Any]) -> None:
        record_observation(
            self.db_path, workspace, category, signal, payload,
        )
        distill_preference(self.db_path, category, signal, payload)

    def reinforce(self, category: str, key: str, delta: int = 5) -> None:
        _reinforce(self.db_path, category, key, delta)

    def weaken(self, category: str, key: str, delta: int = 10) -> None:
        _weaken(self.db_path, category, key, delta)

    def decay_stale(self) -> int:
        return _decay_stale(self.db_path)

    def top_preferences(self, category: Optional[str] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        return _top_preferences(self.db_path, category, limit)

    def render_context(self, limit: int = 8) -> str:
        return _render_context(self.db_path, limit)

    def stats(self) -> Dict[str, Any]:
        return _stats(self.db_path)


__all__ = ["UserProfileStore"]
