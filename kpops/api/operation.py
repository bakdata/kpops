from __future__ import annotations

import enum


class OperationMode(str, enum.Enum):
    ARGO = "argo"
    MANIFEST = "manifest"
    MANAGED = "managed"
