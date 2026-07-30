from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import structlog


class KpopsException(Exception):
    """Base class for all expected, user-facing KPOps errors."""

    logged: bool = False

    def log_extra(self, logger: structlog.stdlib.BoundLogger) -> None:
        """Log extra debug context."""


class ServiceException(KpopsException):
    service: ClassVar[str]


class ValidationError(KpopsException):
    pass


class ParsingException(KpopsException):
    pass


class ClassNotFoundError(KpopsException):
    """Similar to builtin `ModuleNotFoundError`; class doesn't exist inside module."""
