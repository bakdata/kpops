from __future__ import annotations

from typing import TYPE_CHECKING

from kpops.api.operation import OperationMode
from kpops.manifestors.manifestor import Manifestor

if TYPE_CHECKING:
    from kpops.components.base_components import HelmApp
    from kpops.components.base_components.models.resource import Resource


class HelmAppManifestor(Manifestor):
    """Manifestor for the HelmApp component."""

    def generate_annotations(self) -> dict[str, str]:
        """Generate annotations for HelmApp based on operation mode."""
        match self.operation_mode:
            case OperationMode.ARGO:
                return {"argocd.argoproj.io/sync-wave": "1"}
            case _:
                return {}

    def generate_manifest(self, helm_app: HelmApp) -> Resource:
        """Generate the Helm manifest for HelmApp."""
        values = helm_app.to_helm_values()
        annotations = self.generate_annotations()
        if annotations:
            values["annotations"] = annotations

        return helm_app.helm.template(
            helm_app.helm_release_name,
            helm_app.helm_chart,
            helm_app.namespace,
            values,
            helm_app.template_flags,
        )
