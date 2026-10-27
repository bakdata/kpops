from __future__ import annotations

from collections.abc import Mapping, Sequence

# JSON values
type JsonType = (
    Mapping[str, "JsonType"] | Sequence["JsonType"] | str | int | float | bool | None
)
