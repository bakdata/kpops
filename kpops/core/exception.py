from __future__ import annotations

from typing import ClassVar


class KpopsException(Exception):
    """Base class for all expected, user-facing KPOps errors."""

    logged: bool = False


class ServiceException(KpopsException):
    service: ClassVar[str]


class ValidationError(KpopsException):
    pass


class ParsingException(KpopsException):
    pass


class ClassNotFoundError(KpopsException):
    """Similar to builtin `ModuleNotFoundError`; class doesn't exist inside module."""
