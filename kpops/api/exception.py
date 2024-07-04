from __future__ import annotations


class ValidationError(Exception):
    pass


class ParsingException(Exception):
    pass


class ClassNotFoundError(Exception):
    """Similar to builtin `ModuleNotFoundError`; class doesn't exist inside module."""


class InvalidImageTagError(ValidationError):
    def __init__(self, *args):
        super().__init__(*args)
