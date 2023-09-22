"""Documentation generation."""

from collections.abc import Generator
from enum import Enum
from typing import Any


class StrEnum(str, Enum):
    """Adds constructors that return all items in a ``Generator``.

    Introduces constructors that return a ``Generator`` object
    either containing all items, only their names or their values.
    """

    @classmethod
    def items(cls) -> Generator[tuple[Any, str], None, None]:
        """Return all item names and values in tuples."""
        return ((e.name, e.value) for e in cls)

    @classmethod
    def keys(cls) -> Generator[str, None, None]:
        """Return all item names."""
        return (e.name for e in cls)

    @classmethod
    def values(cls) -> Generator[Any, None, None]:
        """Return all item values."""
        return (e.value for e in cls)
