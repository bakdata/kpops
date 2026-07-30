from __future__ import annotations


class KpopsException(Exception):
    """Base class for all expected, user-facing KPOps errors."""

    logged: bool = False
