from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias

# JSON values
JsonType: TypeAlias = (
    Mapping[str, "JsonType"] | Sequence["JsonType"] | str | int | float | bool | None
)
