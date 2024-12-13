"""Documentation generation."""

from collections.abc import Iterator
from enum import StrEnum


class IterableStrEnum(StrEnum):
    """Polyfill that also introduces dict-like behavior.

    Introduces constructors that return a ``Iterator`` object
    either containing all items, only their names or their values.
    """

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
