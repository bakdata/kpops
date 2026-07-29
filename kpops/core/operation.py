from __future__ import annotations

import enum


class OperationMode(enum.StrEnum):
    ARGO = "argo"
    MANIFEST = "manifest"
    MANAGED = "managed"
