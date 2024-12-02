from enum import Enum

from kpops.manifests.kubernetes import KubernetesManifest


class ArgoHook(str, Enum):
    POST_DELETE = "PostDelete"

    @property
    def key(self) -> str:
        return "argocd.argoproj.io/hook"

    def enrich(self, manifest: KubernetesManifest) -> None:
        if manifest.metadata.annotations is None:
            manifest.metadata.annotations = {}
        manifest.metadata.annotations[self.key] = self.value
