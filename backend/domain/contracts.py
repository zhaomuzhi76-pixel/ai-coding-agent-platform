"""DomainProvider protocol: implement per-domain (agriculture/finance/...)."""
from __future__ import annotations

from typing import Dict, List, Optional, Protocol, runtime_checkable

from backend.domain.models import DomainEntity, DomainTerm


@runtime_checkable
class DomainProvider(Protocol):
    """A pluggable domain data source."""

    name: str

    def list_entity_types(self) -> List[str]: ...

    def lookup_entity(
        self, entity_type: str, name: str,
    ) -> Optional[DomainEntity]: ...

    def list_entities(self, entity_type: str) -> List[str]: ...

    def search_entities(
        self, query: str, limit: int = 10,
    ) -> List[DomainEntity]: ...

    def lookup_term(self, name: str) -> Optional[DomainTerm]: ...

    def list_terms(self) -> List[str]: ...

    def ready(self) -> bool: ...

    def dump(self) -> Dict: ...
