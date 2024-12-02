import enum
from typing import Any

from typing_extensions import override


class ArgoEnricher(enum.Enum):
    @property
    def key(self) -> str:
        return NotImplemented

    def enrich(self, helm_values: dict[str, Any]) -> dict[str, Any]:
        annotations = helm_values.setdefault("annotations", {})
        annotations[self.key] = self.value
        return helm_values


class ArgoHook(ArgoEnricher, str, enum.Enum):
    POST_DELETE = "PostDelete"

    @property
    @override
    def key(self) -> str:
        return "argocd.argoproj.io/hook"


class ArgoSyncWave(ArgoEnricher, str, enum.Enum):
    SYNC_WAVE = "1"

    @property
    @override
    def key(self) -> str:
        return "argocd.argoproj.io/sync-wave"
