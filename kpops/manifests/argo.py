import enum
from enum import Enum
from typing import Any


class ArgoEnricher(enum.Enum):
    @property
    def key(self) -> str:
        return NotImplemented

    def enrich(self, helm_values: dict[str, Any]) -> dict[str, Any]:
        annotations = helm_values.setdefault("annotations", {})
        annotations[self.key] = self.value
        return helm_values


class ArgoHook(ArgoEnricher, str, Enum):
    POST_DELETE = "PostDelete"

    @property
    def key(self) -> str:
        return "argocd.argoproj.io/hook"


class ArgoSyncWave(ArgoEnricher, str, Enum):
    SYNC_WAVE = "1"

    @property
    def key(self) -> str:
        return "argocd.argoproj.io/sync-wave"
