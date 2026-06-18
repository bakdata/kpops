from __future__ import annotations

from typing import Any, ClassVar, Self

import pydantic
from pydantic import ConfigDict, Field

from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.components.streams_bootstrap_v2.base import (
    KafkaStreamsConfig,
    StreamsBootstrapV2Values,
)
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
)


class StreamsConfig(KafkaStreamsConfig):
    """streams-bootstrap streams section.

    :param input_topics: Input topics, defaults to []
    :param input_pattern: Input pattern, defaults to None
    :param extra_input_topics: Extra input topics, defaults to {}
    :param extra_input_patterns: Extra input patterns, defaults to {}
    :param error_topic: Error topic, defaults to None
    :param config: Configuration, defaults to {}
    :param delete_output: Whether the output topics with their associated schemas and the consumer group should be deleted during the cleanup, defaults to None
    """

    input_topics: list[KafkaTopicStr] = []
    input_pattern: str | None = None
    extra_input_topics: dict[str, list[KafkaTopicStr]] = {}
    extra_input_patterns: dict[str, str] = {}
    error_topic: KafkaTopicStr | None = None
    config: dict[str, Any] = {}
    delete_output: bool | None = None

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

    enabled: bool = False
    consumer_group: str | None = None
    lag_threshold: int | None = None
    polling_interval: int = 30
    cooldown_period: int = 300
    offset_reset_policy: str = "earliest"
    min_replicas: int = Field(
        default=0,
        title="Min replica count",
    )
    max_replicas: int = Field(
        default=1,
        title="Max replica count",
    )
    idle_replicas: int | None = Field(
        default=None,
        title="Idle replica count",
    )
    topics: list[str] = []

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    @pydantic.model_validator(mode="after")
    def validate_mandatory_fields_are_set(self) -> Self:
        if self.enabled and (self.consumer_group is None or self.lag_threshold is None):
            msg = (
                "If app.autoscaling.enabled is set to true, "
                "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
            )
            raise ValueError(msg)
        return self


class PersistenceConfig(CamelCaseConfigModel, DescConfigModel):
    """streams-bootstrap persistence configurations.

    :param enabled: Whether to use a persistent volume to store the state of the streams app.
    :param size: The size of the PersistentVolume to allocate to each streams pod in the StatefulSet.
    :param storage_class: Storage class to use for the persistent volume.
    """

    enabled: bool = False
    size: str | None = None
    storage_class: str | None = None

    @pydantic.model_validator(mode="after")
    def validate_mandatory_fields_are_set(self) -> Self:
        if self.enabled and self.size is None:
            msg = (
                "If app.persistence.enabled is set to true, "
                "the field app.persistence.size needs to be set."
            )
            raise ValueError(msg)
        return self


class StreamsAppV2Values(StreamsBootstrapV2Values):
    """streams-bootstrap-v2 app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.

    :param streams: streams-bootstrap-v2 streams section
    :param autoscaling: Kubernetes event-driven autoscaling config, defaults to None
    """

    streams: StreamsConfig  # pyright: ignore[reportIncompatibleVariableOverride]
    autoscaling: StreamsAppAutoScaling | None = None
    stateful_set: bool = False
    persistence: PersistenceConfig = PersistenceConfig()

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
