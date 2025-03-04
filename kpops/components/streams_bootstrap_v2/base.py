from __future__ import annotations

import logging
from abc import ABC
from typing import Any, ClassVar, Self

import pydantic
from pydantic import AliasChoices, ConfigDict, Field
from typing_extensions import deprecated

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.components.base_components import KafkaApp
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
from kpops.components.common.kubernetes_model import Affinity, Toleration
from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    SerializeAsOptional,
    SerializeAsOptionalModel,
    SkipGenerate,
    exclude_by_value,
    exclude_defaults,
)

STREAMS_BOOTSTRAP_HELM_REPO = HelmRepoConfig(
    repository_name="bakdata-streams-bootstrap",
    url="https://bakdata.github.io/streams-bootstrap/",
)
STREAMS_BOOTSTRAP_VERSION = "2.9.0"

# Source of the pattern: https://kubernetes.io/docs/concepts/containers/images/#image-names
IMAGE_TAG_PATTERN = r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$"

log = logging.getLogger("StreamsBootstrap")


class KafkaStreamsConfig(CamelCaseConfigModel, DescConfigModel):
    """Kafka Streams config.

    :param brokers: Brokers
    :param schema_registry_url: URL of the schema registry, defaults to None
    :param extra_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    brokers: str = Field(description=describe_attr("brokers", __doc__))
    schema_registry_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "schema_registry_url", "schemaRegistryUrl"
        ),  # TODO: same for other camelcase fields, avoids duplicates during enrichment
        description=describe_attr("schema_registry_url", __doc__),
    )
    extra_output_topics: dict[str, KafkaTopicStr] = Field(
        default={}, description=describe_attr("extra_output_topics", __doc__)
    )
    output_topic: KafkaTopicStr | None = Field(
        default=None,
        description=describe_attr("output_topic", __doc__),
        json_schema_extra={},
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @pydantic.field_validator("extra_output_topics", mode="before")
    @classmethod
    def deserialize_extra_output_topics(
        cls, extra_output_topics: dict[str, str] | Any
    ) -> dict[str, KafkaTopic] | Any:
        if isinstance(extra_output_topics, dict):
            return {
                label: KafkaTopic(name=topic_name)
                for label, topic_name in extra_output_topics.items()
            }
        return extra_output_topics

    @pydantic.field_serializer("extra_output_topics")
    def serialize_extra_output_topics(
        self, extra_topics: dict[str, KafkaTopic]
    ) -> dict[str, str]:
        return {label: topic.name for label, topic in extra_topics.items()}

    # TODO(Ivan Yordanov): Currently hacky and potentially unsafe. Find cleaner solution
    @pydantic.model_serializer(mode="wrap", when_used="always")
    def serialize_model(
        self,
        default_serialize_handler: pydantic.SerializerFunctionWrapHandler,
        info: pydantic.SerializationInfo,
    ) -> dict[str, Any]:
        return exclude_defaults(
            self, exclude_by_value(default_serialize_handler(self), None)
        )


class StreamsBootstrapV2Values(SerializeAsOptionalModel, HelmAppValues):
    """Base value class for all streams bootstrap v2 related components.

    :param image_tag: Docker image tag of the streams-bootstrap-v2 app.
    :param affinity: Map to configure pod affinities https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity.
    :param tolerations: Array containing taint references. When defined, pods can run on nodes, which would otherwise deny scheduling.
    """

    image_tag: str = Field(
        default="latest",
        pattern=IMAGE_TAG_PATTERN,
        description=describe_attr("image_tag", __doc__),
    )

    streams: KafkaStreamsConfig = Field(
        description=describe_attr("streams", __doc__),
    )

    affinity: Affinity | None = Field(
        default=None,
        description=describe_attr("affinity", __doc__),
    )

    tolerations: SerializeAsOptional[list[Toleration]] = Field(
        default=[],
        description=describe_attr("tolerations", __doc__),
    )


@deprecated("StreamsBootstrapV2 component is deprecated, use StreamsBootstrap instead.")
class StreamsBootstrapV2(KafkaApp, HelmApp, ABC):
    """Base for components with a streams-bootstrap-v2 Helm chart.

    :param values: streams-bootstrap-v2 Helm values
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to streams-bootstrap Helm repo
    :param version: Helm chart version, defaults to "2.9.0"
    """

    values: StreamsBootstrapV2Values = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        description=describe_attr("values", __doc__),
    )
    repo_config: SkipGenerate[HelmRepoConfig] = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        default=STREAMS_BOOTSTRAP_HELM_REPO,
        description=describe_attr("repo_config", __doc__),
    )
    version: str | None = Field(
        default=STREAMS_BOOTSTRAP_VERSION,
        description=describe_attr("version", __doc__),
    )

    @pydantic.model_validator(mode="after")
    def warning_for_latest_image_tag(self) -> Self:
        if self.validate_ and self.values.image_tag == "latest":
            log.warning(
                f"The image tag for component '{self.name}' is set or defaulted to 'latest'. Please, consider providing a stable image tag."
            )
        return self

    @pydantic.model_validator(mode="before")
    @classmethod
    def deprecation_warning(cls, model: Any) -> Any:
        log.warning(
            "StreamsBootstrapV2 is deprecated, consider migrating to StreamsBootstrap."
        )
        return model
