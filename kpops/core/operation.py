from __future__ import annotations

import enum


class OperationMode(enum.StrEnum):
    ARGO = enum.auto()
    MANIFEST = enum.auto()
    MANAGED = enum.auto()
