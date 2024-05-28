from __future__ import annotations


class ValidationError(Exception):
    pass


class ParsingException(Exception):
    pass


class ClassNotFoundError(Exception):
    """Similar to builtin `ModuleNotFoundError`; class doesn't exist inside module."""
