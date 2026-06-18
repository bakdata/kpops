from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel


def enrich_annotations(
    helm_values: dict[str, Any], key: str, value: str
) -> dict[str, Any]:
    annotations = helm_values.setdefault("annotations", {})
    annotations[key] = value
    return helm_values


class ArgoHook(str, enum.Enum):
    POST_DELETE = "PostDelete"

    @property
    def key(self) -> str:
        return "argocd.argoproj.io/hook"


class ArgoSyncWave(BaseModel):
    sync_wave: int = 0

    @property
    def key(self) -> str:
        return "argocd.argoproj.io/sync-wave"

    @property
    def value(self) -> str:
        return str(self.sync_wave)
