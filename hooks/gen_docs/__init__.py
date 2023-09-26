"""Documentation generation."""

from collections.abc import Iterator
from enum import Enum


class IterableStrEnum(str, Enum):
    """Temporary replacement for StrEnum while we suppport python3.10"""

    @classmethod
    def items(cls) -> Iterator[tuple[str, str]]:
        """Return all item names and values in tuples."""
        return ((e.name, e.value) for e in cls)

    @classmethod
    def keys(cls) -> Iterator[str]:
        """Return all item names."""
        return (e.name for e in cls)

    @classmethod
    def values(cls) -> Iterator[str]:
        """Return all item values."""
        return (e.value for e in cls)
