from __future__ import annotations

from typing import Any, ClassVar, Self

import pydantic
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.components.streams_bootstrap_v2.base import (
    KafkaStreamsConfig,
    StreamsBootstrapV2Values,
)
from kpops.core.exception import ValidationError
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
)


class StreamsConfig(KafkaStreamsConfig):
    """Streams Bootstrap streams section.

    :param input_topics: Input topics, defaults to []
    :param input_pattern: Input pattern, defaults to None
    :param extra_input_topics: Extra input topics, defaults to {}
    :param extra_input_patterns: Extra input patterns, defaults to {}
    :param error_topic: Error topic, defaults to None
    :param config: Configuration, defaults to {}
    :param delete_output: Whether the output topics with their associated schemas and the consumer group should be deleted during the cleanup, defaults to None
    """

    input_topics: list[KafkaTopicStr] = Field(
        default=[], description=describe_attr("input_topics", __doc__)
    )
    input_pattern: str | None = Field(
        default=None, description=describe_attr("input_pattern", __doc__)
    )
    extra_input_topics: dict[str, list[KafkaTopicStr]] = Field(
        default={}, description=describe_attr("extra_input_topics", __doc__)
    )
    extra_input_patterns: dict[str, str] = Field(
        default={}, description=describe_attr("extra_input_patterns", __doc__)
    )
    error_topic: KafkaTopicStr | None = Field(
        default=None, description=describe_attr("error_topic", __doc__)
    )
    config: dict[str, Any] = Field(
        default={}, description=describe_attr("config", __doc__)
    )
    delete_output: bool | None = Field(
        default=None, description=describe_attr("delete_output", __doc__)
    )

    @pydantic.field_validator("input_topics", mode="before")
    @classmethod
    def deserialize_input_topics(
        cls, input_topics: list[str] | Any
    ) -> list[KafkaTopic] | Any:
        if isinstance(input_topics, list):
            return [KafkaTopic(name=topic_name) for topic_name in input_topics]
        return input_topics

    @pydantic.field_validator("extra_input_topics", mode="before")
    @classmethod
    def deserialize_extra_input_topics(
        cls, extra_input_topics: dict[str, str] | Any
    ) -> dict[str, list[KafkaTopic]] | Any:
        if isinstance(extra_input_topics, dict):
            return {
                label: [KafkaTopic(name=topic_name) for topic_name in topics]
                for label, topics in extra_input_topics.items()
            }
        return extra_input_topics

    @pydantic.field_serializer("input_topics")
    def serialize_topics(self, topics: list[KafkaTopic]) -> list[str]:
        return [topic.name for topic in topics]

    @pydantic.field_serializer("extra_input_topics")
    def serialize_extra_input_topics(
        self, extra_topics: dict[str, list[KafkaTopic]]
    ) -> dict[str, list[str]]:
        return {
            label: self.serialize_topics(topics)
            for label, topics in extra_topics.items()
        }

    def add_input_topics(self, topics: list[KafkaTopic]) -> None:
        """Add given topics to the list of input topics.

        Ensures no duplicate topics in the list.

        :param topics: Input topics
        """
        self.input_topics = KafkaTopic.deduplicate(self.input_topics + topics)

    def add_extra_input_topics(self, label: str, topics: list[KafkaTopic]) -> None:
        """Add given extra topics that share a label to the list of extra input topics.

        Ensures no duplicate topics in the list.

        :param topics: Extra input topics
        :param label: Topic label
        """
        self.extra_input_topics[label] = KafkaTopic.deduplicate(
            self.extra_input_topics.get(label, []) + topics
        )


class StreamsAppAutoScaling(CamelCaseConfigModel, DescConfigModel):
    """Kubernetes Event-driven Autoscaling config.

    :param enabled: Whether to enable auto-scaling using KEDA., defaults to False
    :param consumer_group: Name of the consumer group used for checking the
        offset on the topic and processing the related lag.
        Mandatory to set when auto-scaling is enabled.
    :param lag_threshold: Average target value to trigger scaling actions.
        Mandatory to set when auto-scaling is enabled.
    :param polling_interval: This is the interval to check each trigger on.
        https://keda.sh/docs/2.9/concepts/scaling-deployments/#pollinginterval,
        defaults to 30
    :param cooldown_period: The period to wait after the last trigger reported
        active before scaling the resource back to 0.
        https://keda.sh/docs/2.9/concepts/scaling-deployments/#cooldownperiod,
        defaults to 300
    :param offset_reset_policy: The offset reset policy for the consumer if the
        consumer group is not yet subscribed to a partition.,
        defaults to "earliest"
    :param min_replicas: Minimum number of replicas KEDA will scale the resource down to.
        "https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount",
        defaults to 0
    :param max_replicas: This setting is passed to the HPA definition that KEDA
        will create for a given resource and holds the maximum number of replicas
        of the target resouce.
        https://keda.sh/docs/2.9/concepts/scaling-deployments/#maxreplicacount,
        defaults to 1
    :param idle_replicas: If this property is set, KEDA will scale the resource
        down to this number of replicas.
        https://keda.sh/docs/2.9/concepts/scaling-deployments/#idlereplicacount,
        defaults to None
    :param topics: List of auto-generated Kafka Streams topics used by the streams app.,
        defaults to []
    """

    enabled: bool = Field(
        default=False,
        description=describe_attr("streams", __doc__),
    )
    consumer_group: str | None = Field(
        default=None,
        title="Consumer group",
        description=describe_attr("consumer_group", __doc__),
    )
    lag_threshold: int | None = Field(
        default=None,
        title="Lag threshold",
        description=describe_attr("lag_threshold", __doc__),
    )
    polling_interval: int = Field(
        default=30,
        title="Polling interval",
        description=describe_attr("polling_interval", __doc__),
    )
    cooldown_period: int = Field(
        default=300,
        title="Cooldown period",
        description=describe_attr("cooldown_period", __doc__),
    )
    offset_reset_policy: str = Field(
        default="earliest",
        title="Offset reset policy",
        description=describe_attr("offset_reset_policy", __doc__),
    )
    min_replicas: int = Field(
        default=0,
        title="Min replica count",
        description=describe_attr("min_replicas", __doc__),
    )
    max_replicas: int = Field(
        default=1,
        title="Max replica count",
        description=describe_attr("max_replicas", __doc__),
    )
    idle_replicas: int | None = Field(
        default=None,
        title="Idle replica count",
        description=describe_attr("idle_replicas", __doc__),
    )
    topics: list[str] = Field(
        default=[],
        description=describe_attr("topics", __doc__),
    )
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_mandatory_fields_are_set(self) -> Self:
        if self.enabled and (self.consumer_group is None or self.lag_threshold is None):
            msg = (
                "If app.autoscaling.enabled is set to true, "
                "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
            )
            raise ValidationError(msg)
        return self


class PersistenceConfig(BaseModel):
    """streams-bootstrap persistence configurations.

    :param enabled: Whether to use a persistent volume to store the state of the streams app.
    :param size: The size of the PersistentVolume to allocate to each streams pod in the StatefulSet.
    :param storage_class: Storage class to use for the persistent volume.
    """

    enabled: bool = Field(
        default=False,
        description="Whether to use a persistent volume to store the state of the streams app.	",
    )
    size: str | None = Field(
        default=None,
        description="The size of the PersistentVolume to allocate to each streams pod in the StatefulSet.",
    )
    storage_class: str | None = Field(
        default=None,
        description="Storage class to use for the persistent volume.",
    )

    @model_validator(mode="after")
    def validate_mandatory_fields_are_set(self) -> Self:
        if self.enabled and self.size is None:
            msg = (
                "If app.persistence.enabled is set to true, "
                "the field app.persistence.size needs to be set."
            )
            raise ValidationError(msg)
        return self


class StreamsAppV2Values(StreamsBootstrapV2Values):
    """streams-bootstrap-v2 app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.

    :param streams: streams-bootstrap-v2 streams section
    :param autoscaling: Kubernetes event-driven autoscaling config, defaults to None
    """

    streams: StreamsConfig = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        description=describe_attr("streams", __doc__),
    )
    autoscaling: StreamsAppAutoScaling | None = Field(
        default=None,
        description=describe_attr("autoscaling", __doc__),
    )
    stateful_set: bool = Field(
        default=False,
        description="Whether to use a Statefulset instead of a Deployment to deploy the streams app.",
    )
    persistence: PersistenceConfig = Field(
        default=PersistenceConfig(),
        description=describe_attr("persistence", __doc__),
    )
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
