"""Domain layer: pluggable domain data providers (agriculture/finance/...)."""
from backend.domain.models import DomainEntity, DomainTerm
from backend.domain.contracts import DomainProvider
from backend.domain.registry import DomainRegistry

__all__ = ["DomainEntity", "DomainTerm", "DomainProvider", "DomainRegistry"]
