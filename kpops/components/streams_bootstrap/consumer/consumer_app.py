from functools import cached_property

import structlog
from pydantic import Field, ValidationError
from typing_extensions import override

from kpops.component_handlers.kubernetes.pvc_handler import PVCHandler
from kpops.components.base_components.helm_app import HelmApp
from kpops.components.common.app_type import AppType
from kpops.components.common.topic import KafkaTopic
from kpops.components.streams_bootstrap.base import (
    StreamsBootstrap,
    StreamsBootstrapCleaner,
)
from kpops.components.streams_bootstrap.consumer.model import ConsumerAppValues
from kpops.config import get_config
from kpops.const.file_type import DEFAULTS_YAML, PIPELINE_YAML
from kpops.core.operation import OperationMode
from kpops.manifests.argo import ArgoHook, enrich_annotations
from kpops.manifests.kubernetes import KubernetesManifest

log = structlog.get_logger("ConsumerApp")


class ConsumerAppCleaner(StreamsBootstrapCleaner, StreamsBootstrap):
    values: ConsumerAppValues

    @property
    @override
    def helm_chart(self) -> str:
        return (
            f"{self.repo_config.repository_name}/{AppType.CLEANUP_CONSUMER_APP.value}"
        )

    @override
    async def reset(self, dry_run: bool) -> None:
        await super().clean(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        await super().clean(dry_run)

        if (
            self.values.stateful_set
            and self.values.persistence
            and self.values.persistence.enabled
        ):
            await self.clean_pvcs(dry_run)

    @override
    def manifest_deploy(self) -> tuple[KubernetesManifest, ...]:
        values = self.to_helm_values()
        if get_config().operation_mode is OperationMode.ARGO:
            post_delete = ArgoHook.POST_DELETE
            values = enrich_annotations(values, post_delete.key, post_delete.value)
        return self._helm.template(
            self.helm_release_name,
            self.helm_chart,
            self.namespace,
            values,
            self.template_flags,
        )

    @override
    def manifest_reset(self) -> tuple[KubernetesManifest, ...]:
        values = self.to_helm_values()

        return self._helm.template(
            self.helm_release_name,
            self.helm_chart,
            self.namespace,
            values,
            self.template_flags,
        )

    async def clean_pvcs(self, dry_run: bool) -> None:
        app_full_name = super(HelmApp, self).full_name
        pvc_handler = PVCHandler(app_full_name, self.namespace)
        await pvc_handler.delete_pvcs(dry_run)


class ConsumerApp(StreamsBootstrap):
    """StreamsApp component that configures a streams-bootstrap app.

    :param values: streams-bootstrap Helm values
    """

    values: ConsumerAppValues
    to: None = Field(
        default=None,
        alias="to",
        title="To",
    )

    @cached_property
    def _cleaner(self) -> ConsumerAppCleaner:
        return ConsumerAppCleaner.from_parent(self)

    @property
    @override
    def input_topics(self) -> list[KafkaTopic]:
        return self.values.kafka.input_topics

    @property
    @override
    def extra_input_topics(self) -> dict[str, list[KafkaTopic]]:
        return self.values.kafka.labeled_input_topics

    @override
    def add_input_topics(self, topics: list[KafkaTopic]) -> None:
        self.values.kafka.add_input_topics(topics)

    @override
    def add_extra_input_topics(self, label: str, topics: list[KafkaTopic]) -> None:
        self.values.kafka.add_labeled_input_topics(label, topics)

    @override
    def set_input_pattern(self, name: str) -> None:
        self.values.kafka.input_pattern = name

    @override
    def add_extra_input_pattern(self, label: str, topic: str) -> None:
        self.values.kafka.labeled_input_patterns[label] = topic

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.CONSUMER_APP.value}"

    @override
    async def destroy(self, dry_run: bool) -> None:
        cluster_values = await self._helm.get_values(
            self.namespace, self.helm_release_name
        )
        if cluster_values:
            log.debug("Fetched Helm chart values from cluster")
            name_override = self._cleaner.helm_name_override
            try:
                self._cleaner.values = self.values.model_validate(cluster_values)
                self._cleaner.values.name_override = name_override
                self._cleaner.values.fullname_override = name_override
            except ValidationError as validation_error:
                log.warning(
                    f"The values in the cluster are invalid with the current model. Falling back to the enriched values of {PIPELINE_YAML} and {DEFAULTS_YAML}"
                )
                log.debug("Cluster values", values=cluster_values)
                log.debug("Validation error", error=validation_error)

        await super().destroy(dry_run)

    @override
    async def reset(self, dry_run: bool) -> None:
        """Destroy and reset."""
        await super().reset(dry_run)
        await self._cleaner.reset(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        """Destroy and clean."""
        await super().clean(dry_run)
        await self._cleaner.clean(dry_run)

    @override
    def manifest_deploy(self) -> tuple[KubernetesManifest, ...]:
        manifests = super().manifest_deploy()
        if get_config().operation_mode is OperationMode.ARGO:
            manifests = manifests + self._cleaner.manifest_deploy()

        return manifests

    @override
    def manifest_reset(self) -> tuple[KubernetesManifest, ...]:
        return self._cleaner.manifest_reset()

    @override
    def manifest_clean(self) -> tuple[KubernetesManifest, ...]:
        if get_config().operation_mode is OperationMode.MANIFEST:
            return self._cleaner.manifest_deploy()
        return ()
