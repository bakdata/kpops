from __future__ import annotations

import enum

from pydantic import BaseModel, Field

try:
    from typing import Any, Self  # pyright: ignore[reportAttributeAccessIssue]
except ImportError:
    from typing_extensions import Self


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
    sync_wave: int = Field(default=0, serialization_alias="SyncWave")

    @property
    def key(self) -> str:
        return "argocd.argoproj.io/sync-wave"

    @property
    def value(self) -> str:
        return str(self.sync_wave)

    @classmethod
    def create(cls, sync_wave: int) -> Self:
        return cls(**{"SyncWave": sync_wave})
