from __future__ import annotations

from typing import ClassVar


class KpopsException(Exception):
    """Base class for all expected, user-facing KPOps errors."""

    logged: bool = False


class ServiceException(KpopsException):
    service: ClassVar[str]
