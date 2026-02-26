from typing import Annotated, Any, ClassVar

import pydantic
from pydantic import ConfigDict, Field

from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.components.streams_bootstrap.common.model import (
    JMXConfig,
    PersistenceConfig,
    PrometheusExporterConfig,
    StreamsAppAutoScaling,
    serialize_labeled_input_topics,
    serialize_topics,
)
from kpops.components.streams_bootstrap.model import KafkaConfig, StreamsBootstrapValues
from kpops.utils.pydantic import (
    SerializeAsOptional,
)


class ConsumerConfig(KafkaConfig):
    """consuemr app kafka section.

    :param group_id: Unique consumer group ID for Kafka Streams. Required for auto-scaling #TODO true?
    :param input_topics: Input topics, defaults to []
    :param input_pattern: Input pattern, defaults to None
    :param labeled_input_topics: Extra input topics, defaults to {}
    :param labeled_input_patterns: Extra input patterns, defaults to {}
    :param config: Configuration, defaults to {}
    """

    group_id: str | None = Field(default=None, title="Unique consuemer group ID")
    input_topics: SerializeAsOptional[
        Annotated[
            list[KafkaTopicStr],
            pydantic.PlainSerializer(serialize_topics),
        ]
    ] = []
    input_pattern: str | None = None
    labeled_input_topics: SerializeAsOptional[
        Annotated[
            dict[str, list[KafkaTopicStr]],
            pydantic.PlainSerializer(serialize_labeled_input_topics),
        ]
    ] = {}
    labeled_input_patterns: SerializeAsOptional[dict[str, str]] = {}
    config: SerializeAsOptional[dict[str, Any]] = {}

    @pydantic.field_validator("input_topics", mode="before")
    @classmethod
    def deserialize_input_topics(
        cls, input_topics: list[str] | Any
    ) -> list[KafkaTopic] | Any:
        if isinstance(input_topics, list):
            return [KafkaTopic(name=topic_name) for topic_name in input_topics]
        return input_topics

    @pydantic.field_validator("labeled_input_topics", mode="before")
    @classmethod
    def deserialize_labeled_input_topics(
        cls, labeled_input_topics: dict[str, list[str]] | Any
    ) -> dict[str, list[KafkaTopic]] | Any:
        if isinstance(labeled_input_topics, dict):
            return {
                label: [KafkaTopic(name=topic_name) for topic_name in topics]
                for label, topics in labeled_input_topics.items()
            }
        return labeled_input_topics

    def add_input_topics(self, topics: list[KafkaTopic]) -> None:
        """Add given topics to the list of input topics.

        Ensures no duplicate topics in the list.

        :param topics: Input topics
        """
        self.input_topics = KafkaTopic.deduplicate(self.input_topics + topics)

    def add_labeled_input_topics(self, label: str, topics: list[KafkaTopic]) -> None:
        """Add given labeled topics that share a label to the list of extra input topics.

        Ensures no duplicate topics in the list.

        :param topics: Extra input topics
        :param label: Topic label
        """
        self.labeled_input_topics[label] = KafkaTopic.deduplicate(
            self.labeled_input_topics.get(label, []) + topics
        )


class ConsumerAppValues(StreamsBootstrapValues):
    """consumer-app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.

    :param kafka: consumer-app kafka section
    :param autoscaling: Kubernetes event-driven autoscaling config, defaults to None
    :param stateful_set: Whether to use a StatefulSet instead of a Deployment to deploy the consumer app.
    :param persistence: Configuration for persistent volume to store the state of the consumer app.
    :param prometheus: Configuration for Prometheus JMX Exporter.
    :param jmx: Configuration for JMX Exporter.
    :param termination_grace_period_seconds: Delay for graceful application shutdown in seconds: https://pracucci.com/graceful-shutdown-of-kubernetes-pods.html
    """

    kafka: ConsumerConfig = ConsumerConfig()  # pyright: ignore[reportIncompatibleVariableOverride]
    autoscaling: StreamsAppAutoScaling | None = None
    stateful_set: bool = False
    persistence: PersistenceConfig | None = None
    prometheus: PrometheusExporterConfig | None = None
    jmx: JMXConfig | None = None
    termination_grace_period_seconds: int | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
