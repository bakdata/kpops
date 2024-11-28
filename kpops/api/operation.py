from __future__ import annotations

from enum import Enum


class OperationMode(str, Enum):
    ARGO = "argo"
    MANIFEST = "manifest"
    STANDARD = "standard"
