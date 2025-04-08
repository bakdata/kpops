import logging
from functools import cached_property

from pydantic import Field, ValidationError
from typing_extensions import override

from kpops.component_handlers.kubernetes.utils import trim
from kpops.components.common.app_type import AppType
from kpops.components.common.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap.base import (
    StreamsBootstrap,
    StreamsBootstrapCleaner,
)
from kpops.components.streams_bootstrap.producer.model import ProducerAppValues
from kpops.config import get_config
from kpops.const.file_type import DEFAULTS_YAML, PIPELINE_YAML
from kpops.core.operation import OperationMode
from kpops.manifests.argo import ArgoHook, enrich_annotations
from kpops.manifests.kubernetes import K8S_CRON_JOB_NAME_MAX_LEN, KubernetesManifest
from kpops.manifests.strimzi.kafka_topic import StrimziKafkaTopic
from kpops.utils.docstring import describe_attr

log = logging.getLogger("ProducerApp")


class ProducerAppCleaner(StreamsBootstrapCleaner, StreamsBootstrap):  # pyright: ignore[reportIncompatibleVariableOverride]
    values: ProducerAppValues  # pyright: ignore[reportIncompatibleVariableOverride]

    @property
    @override
    def helm_chart(self) -> str:
        return (
            f"{self.repo_config.repository_name}/{AppType.CLEANUP_PRODUCER_APP.value}"
        )

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


class ProducerApp(StreamsBootstrap):
    """Producer component.

    This producer holds configuration to use as values for the streams-bootstrap
    producer Helm chart.

    Note that the producer does not support error topics.

    :param values: streams-bootstrap Helm values
    :param from_: Producer doesn't support FromSection, defaults to None
    """

    values: ProducerAppValues = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        description=describe_attr("values", __doc__),
    )
    from_: None = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        default=None,
        alias="from",
        title="From",
        description=describe_attr("from_", __doc__),
    )

    @property
    def is_cron_job(self) -> bool:
        return bool(not self.values.deployment and self.values.schedule)

    @cached_property
    def _cleaner(self) -> ProducerAppCleaner:
        return ProducerAppCleaner.from_parent(self)

    @override
    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        match topic.type:
            case OutputTopicTypes.ERROR:
                msg = "Producer apps do not support error topics"
                raise ValueError(msg)
            case _:
                super().apply_to_outputs(name, topic)

    @property
    @override
    def helm_name_override(self) -> str:
        if self.is_cron_job:
            return trim(K8S_CRON_JOB_NAME_MAX_LEN, self.full_name, "")
        return super().helm_name_override

    @property
    @override
    def output_topic(self) -> KafkaTopic | None:
        return self.values.kafka.output_topic

    @property
    @override
    def extra_output_topics(self) -> dict[str, KafkaTopic]:
        return self.values.kafka.labeled_output_topics

    @override
    def set_output_topic(self, topic: KafkaTopic) -> None:
        self.values.kafka.output_topic = topic

    @override
    def add_extra_output_topic(self, topic: KafkaTopic, label: str) -> None:
        self.values.kafka.labeled_output_topics[label] = topic

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.PRODUCER_APP.value}"

    @override
    async def reset(self, dry_run: bool) -> None:
        """Reset not necessary, since producer app has no consumer group offsets."""
        await super().reset(dry_run)

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
                warning_msg = f"The values in the cluster are invalid with the current model. Falling back to the enriched values of {PIPELINE_YAML} and {DEFAULTS_YAML}"
                log.warning(warning_msg)
                debug_msg = f"Cluster values: {cluster_values}"
                log.debug(debug_msg)
                debug_msg = f"Validation error: {validation_error}"
                log.debug(debug_msg)

        await super().destroy(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        """Destroy and clean."""
        await super().clean(dry_run)
        await self._cleaner.clean(dry_run)

    @override
    def manifest_deploy(self) -> tuple[KubernetesManifest, ...]:
        manifests = super().manifest_deploy()
        operation_mode = get_config().operation_mode

        if operation_mode is OperationMode.ARGO:
            manifests = manifests + self._cleaner.manifest_deploy()

        return manifests

    @override
    def manifest_reset(self) -> tuple[KubernetesManifest, ...]:
        if self.to:
            return tuple(
                StrimziKafkaTopic.from_topic(topic) for topic in self.to.kafka_topics
            )
        return ()

    @override
    def manifest_clean(self) -> tuple[KubernetesManifest, ...]:
        if get_config().operation_mode is OperationMode.MANIFEST:
            return self._cleaner.manifest_deploy()
        return ()
