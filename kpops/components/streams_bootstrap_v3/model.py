from __future__ import annotations

from typing import Any

import pydantic
from pydantic import AliasChoices, ConfigDict, Field

from kpops.components.base_components.helm_app import HelmAppValues
from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    exclude_by_value,
    exclude_defaults,
)

# Source of the pattern: https://kubernetes.io/docs/concepts/containers/images/#image-names
IMAGE_TAG_PATTERN = r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$"


class StreamsBootstrapValues(HelmAppValues):
    """Base value class for all streams bootstrap related components.

    :param image_tag: Docker image tag of the streams-bootstrap app.
    :param kafka: Kafka configuration for the streams-bootstrap app.
    """

    image_tag: str = Field(
        default="latest",
        pattern=IMAGE_TAG_PATTERN,
        description=describe_attr("image_tag", __doc__),
    )

    kafka: KafkaConfig = Field(
        default=...,
        description=describe_attr("kafka", __doc__),
    )


class KafkaConfig(CamelCaseConfigModel, DescConfigModel):
    """Kafka Streams config.

    :param bootstrap_servers: Brokers
    :param schema_registry_url: URL of the schema registry, defaults to None
    :param labeled_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    bootstrap_servers: str = Field(
        default=..., description=describe_attr("bootstrap_servers", __doc__)
    )
    schema_registry_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "schema_registry_url", "schemaRegistryUrl"
        ),  # TODO: same for other camelcase fields, avoids duplicates during enrichment
        description=describe_attr("schema_registry_url", __doc__),
    )
    labeled_output_topics: dict[str, KafkaTopicStr] = Field(
        default={}, description=describe_attr("labeled_output_topics", __doc__)
    )
    output_topic: KafkaTopicStr | None = Field(
        default=None,
        description=describe_attr("output_topic", __doc__),
        json_schema_extra={},
    )

    model_config = ConfigDict(extra="allow")

    @pydantic.field_validator("labeled_output_topics", mode="before")
    @classmethod
    def deserialize_labeled_output_topics(
        cls, labeled_output_topics: dict[str, str] | Any
    ) -> dict[str, KafkaTopic] | Any:
        if isinstance(labeled_output_topics, dict):
            return {
                label: KafkaTopic(name=topic_name)
                for label, topic_name in labeled_output_topics.items()
            }
        return labeled_output_topics

    @pydantic.field_serializer("labeled_output_topics")
    def serialize_labeled_output_topics(
        self, labeled_output_topics: dict[str, KafkaTopic]
    ) -> dict[str, str]:
        return {label: topic.name for label, topic in labeled_output_topics.items()}

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
