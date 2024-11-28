from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from kpops.api.operation import OperationMode
from kpops.components.base_components.models.resource import Resource
from kpops.manifestors.helm_app_manifestor import HelmAppManifestor

if TYPE_CHECKING:
    from kpops.components.streams_bootstrap.streams.streams_app import StreamsAppCleaner


class StreamsAppCleanerManifestor(HelmAppManifestor):
    """Manifestor for the StreamsApp cleaner component."""

    @override
    def generate_annotations(self) -> dict[str, str]:
        """Generate annotations for StreamsApp based on operation mode."""
        match self.operation_mode:
            case OperationMode.ARGO:
                return {"argocd.argoproj.io/hook": "PostDelete"}
            case _:
                return {}

    @override
    def generate_manifest(self, cleaner: StreamsAppCleaner) -> Resource:
        """Generate the Helm manifest for StreamsApp."""
        values = cleaner.to_helm_values()
        annotations = self.generate_annotations()
        if annotations:
            values["annotations"] = annotations

        return cleaner.helm.template(
            cleaner.helm_release_name,
            cleaner.helm_chart,
            cleaner.namespace,
            values,
            cleaner.template_flags,
        )
