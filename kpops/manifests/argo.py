import enum
from typing import Any

from typing_extensions import override


class ArgoEnricher:
    @property
    def key(self) -> str:
        return NotImplemented

    @property
    def value(self) -> str:
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

    @property
    @override
    def value(self) -> str:
        return self.POST_DELETE._value_


class ArgoSyncWave(ArgoEnricher):
    sync_wave: int

    def __init__(self, sync_wave: int) -> None:
        self.sync_wave = sync_wave

    @property
    @override
    def key(self) -> str:
        return "argocd.argoproj.io/sync-wave"

    @property
    @override
    def value(self) -> str:
        return str(self.sync_wave)
