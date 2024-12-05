from __future__ import annotations

from typing import Any

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from kpops.components.common.kubernetes_model import (
    ImagePullPolicy,
    Resources,
)
from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.components.streams_bootstrap.model import (
    KafkaConfig,
    StreamsBootstrapValues,
)
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
)


class StreamsConfig(KafkaConfig):
    """Streams Bootstrap kafka section.

    :param application_id: Unique application ID for Kafka Streams. Required for auto-scaling
    :param input_topics: Input topics, defaults to []
    :param input_pattern: Input pattern, defaults to None
    :param labeled_input_topics: Extra input topics, defaults to {}
    :param labeled_input_patterns: Extra input patterns, defaults to {}
    :param error_topic: Error topic, defaults to None
    :param config: Configuration, defaults to {}
    :param delete_output: Whether the output topics with their associated schemas and the consumer group should be deleted during the cleanup, defaults to None
    """

    application_id: str | None = Field(
        default=None,
        title="Unique application ID",
        description=describe_attr("application_id", __doc__),
    )
    input_topics: list[KafkaTopicStr] = Field(
        default=[], description=describe_attr("input_topics", __doc__)
    )
    input_pattern: str | None = Field(
        default=None, description=describe_attr("input_pattern", __doc__)
    )
    labeled_input_topics: dict[str, list[KafkaTopicStr]] = Field(
        default={}, description=describe_attr("labeled_input_topics", __doc__)
    )
    labeled_input_patterns: dict[str, str] = Field(
        default={}, description=describe_attr("labeled_input_patterns", __doc__)
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

    @pydantic.field_serializer("input_topics")
    def serialize_topics(self, input_topics: list[KafkaTopic]) -> list[str]:
        return [topic.name for topic in input_topics]

    @pydantic.field_serializer("labeled_input_topics")
    def serialize_labeled_input_topics(
        self, labeled_input_topics: dict[str, list[KafkaTopic]]
    ) -> dict[str, list[str]]:
        return {
            label: self.serialize_topics(topics)
            for label, topics in labeled_input_topics.items()
        }

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


class StreamsAppAutoScaling(CamelCaseConfigModel, DescConfigModel):
    """Kubernetes Event-driven Autoscaling config.

    :param enabled: Whether to enable auto-scaling using KEDA., defaults to False
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
    :param internal_topics: List of auto-generated Kafka Streams topics used by the streams app, defaults to []
    :param topics: List of topics used by the streams app, defaults to []
    :param additional_triggers: List of additional KEDA triggers,
        see https://keda.sh/docs/latest/scalers/,
        defaults to []
    """

    enabled: bool = Field(
        default=False,
        description=describe_attr("enabled", __doc__),
    )
    lag_threshold: int | None = Field(
        default=None,
        title="Lag threshold",
        description=describe_attr("lag_threshold", __doc__),
    )
    polling_interval: int | None = Field(
        default=None,
        title="Polling interval",
        description=describe_attr("polling_interval", __doc__),
    )
    cooldown_period: int | None = Field(
        default=None,
        title="Cooldown period",
        description=describe_attr("cooldown_period", __doc__),
    )
    offset_reset_policy: str | None = Field(
        default=None,
        title="Offset reset policy",
        description=describe_attr("offset_reset_policy", __doc__),
    )
    min_replicas: int | None = Field(
        default=None,
        title="Min replica count",
        description=describe_attr("min_replicas", __doc__),
    )
    max_replicas: int | None = Field(
        default=None,
        title="Max replica count",
        description=describe_attr("max_replicas", __doc__),
    )
    idle_replicas: int | None = Field(
        default=None,
        title="Idle replica count",
        description=describe_attr("idle_replicas", __doc__),
    )
    internal_topics: list[str] | None = Field(
        default=None,
        description=describe_attr("internal_topics", __doc__),
    )
    topics: list[str] | None = Field(
        default=None,
        description=describe_attr("topics", __doc__),
    )
    additional_triggers: list[str] | None = Field(
        default=None,
        description=describe_attr("additional_triggers", __doc__),
    )
    model_config = ConfigDict(extra="allow")


class PersistenceConfig(BaseModel):
    """streams-bootstrap persistence configurations.

    :param enabled: Whether to use a persistent volume to store the state of the streams app.
    :param size: The size of the PersistentVolume to allocate to each streams pod in the StatefulSet.
    :param storage_class: Storage class to use for the persistent volume.
    """

    enabled: bool = Field(
        default=False,
        description="Whether to use a persistent volume to store the state of the streams app.",
    )
    size: str | None = Field(
        default=None,
        description="The size of the PersistentVolume to allocate to each streams pod in the StatefulSet.",
    )
    storage_class: str | None = Field(
        default=None,
        description="Storage class to use for the persistent volume.",
    )


class PrometheusExporterConfig(CamelCaseConfigModel, DescConfigModel):
    """Prometheus JMX exporter configuration.

    :param jmx: The prometheus JMX exporter configuration.

    """

    class PrometheusJMXExporterConfig(CamelCaseConfigModel, DescConfigModel):
        """Prometheus JMX exporter configuration.

        :param enabled: Whether to install Prometheus JMX Exporter as a sidecar container and expose JMX metrics to Prometheus.
        :param image: Docker Image for Prometheus JMX Exporter container.
        :param image_tag: Docker Image Tag for Prometheus JMX Exporter container.
        :param image_pull_policy: Docker Image Pull Policy for Prometheus JMX Exporter container.
        :param port: JMX Exporter Port which exposes metrics in Prometheus format for scraping.
        :param resources: JMX Exporter resources configuration.
        """

        enabled: bool | None = Field(
            default=None,
            description=describe_attr("enabled", __doc__),
        )
        image: str | None = Field(
            default=None,
            description=describe_attr("image", __doc__),
        )
        image_tag: str | None = Field(
            default=None,
            description=describe_attr("image_tag", __doc__),
        )
        image_pull_policy: ImagePullPolicy | None = Field(
            default=None,
            description=describe_attr("image_pull_policy", __doc__),
        )
        port: int | None = Field(
            default=None,
            description=describe_attr("port", __doc__),
        )
        resources: Resources | None = Field(
            default=None,
            description=describe_attr("resources", __doc__),
        )

    jmx: PrometheusJMXExporterConfig | None = Field(
        default=None,
        description=describe_attr("jmx", __doc__),
    )


class JMXConfig(CamelCaseConfigModel, DescConfigModel):
    """JMX configuration options.

    :param port: The jmx port which JMX style metrics are exposed.
    :param metric_rules: List of JMX metric rules.
    """

    port: int | None = Field(
        default=None,
        description=describe_attr("port", __doc__),
    )

    metric_rules: list[str] | None = Field(
        default=None,
        description=describe_attr("metric_rules", __doc__),
    )


class StreamsAppValues(StreamsBootstrapValues):
    """streams-bootstrap app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.

    :param kafka: streams-bootstrap kafka section
    :param autoscaling: Kubernetes event-driven autoscaling config, defaults to None
    :param stateful_set: Whether to use a StatefulSet instead of a Deployment to deploy the streams app.
    :param persistence: Configuration for persistent volume to store the state of the streams app.
    :param prometheus: Configuration for Prometheus JMX Exporter.
    :param jmx: Configuration for JMX Exporter.
    :param termination_grace_period_seconds: Delay for graceful application shutdown in seconds: https://pracucci.com/graceful-shutdown-of-kubernetes-pods.html
    """

    kafka: StreamsConfig = Field(
        description=describe_attr("kafka", __doc__),
    )

    autoscaling: StreamsAppAutoScaling | None = Field(
        default=None,
        description=describe_attr("autoscaling", __doc__),
    )

    stateful_set: bool = Field(
        default=False,
        description=describe_attr("stateful_set", __doc__),
    )

    persistence: PersistenceConfig | None = Field(
        default=None,
        description=describe_attr("persistence", __doc__),
    )

    prometheus: PrometheusExporterConfig | None = Field(
        default=None,
        description=describe_attr("prometheus", __doc__),
    )

    jmx: JMXConfig | None = Field(
        default=None,
        description=describe_attr("jmx", __doc__),
    )

    termination_grace_period_seconds: int | None = Field(
        default=None,
        description=describe_attr("termination_grace_period_seconds", __doc__),
    )

    model_config = ConfigDict(extra="allow")
