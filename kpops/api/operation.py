from __future__ import annotations

from enum import StrEnum


class OperationMode(StrEnum):
    ARGO = "argo"
    MANIFEST = "manifest"
    MANAGED = "managed"
