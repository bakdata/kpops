"""Documentation generation."""

from collections.abc import Generator
from enum import Enum
from typing import Any


class StrEnum(str, Enum):
    """Temporary replacement for StrEnum while we suppport python3.10"""

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
