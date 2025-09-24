from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, ClassVar, Self

import pydantic
from pydantic import ConfigDict, Field

from kpops.components.common.kubernetes_model import (
    ImagePullPolicy,
    Resources,
)
from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.components.streams_bootstrap.model import (
    KafkaConfig,
    StreamsBootstrapValues,
)
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    SerializeAsOptional,
    SerializeAsOptionalModel,
)


def serialize_topics(topics: list[KafkaTopic]) -> list[str]:
    return [topic.name for topic in topics]


def serialize_labeled_input_topics(
    labeled_input_topics: dict[str, list[KafkaTopic]],
) -> dict[str, list[str]]:
    return {
        label: serialize_topics(topics)
        for label, topics in labeled_input_topics.items()
    }


class StreamsConfig(KafkaConfig):
    """streams-bootstrap kafka section.

    :param application_id: Unique application ID for Kafka Streams. Required for auto-scaling
    :param input_topics: Input topics, defaults to []
    :param input_pattern: Input pattern, defaults to None
    :param labeled_input_topics: Extra input topics, defaults to {}
    :param labeled_input_patterns: Extra input patterns, defaults to {}
    :param error_topic: Error topic, defaults to None
    :param config: Configuration, defaults to {}
    :param delete_output: Whether the output topics with their associated schemas and the consumer group should be deleted during the cleanup, defaults to None
    """

    application_id: str | None = Field(default=None, title="Unique application ID")
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
    error_topic: KafkaTopicStr | None = None
    config: SerializeAsOptional[dict[str, Any]] = {}
    delete_output: bool | None = None

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


class StreamsAppAutoScaling(
    SerializeAsOptionalModel, CamelCaseConfigModel, DescConfigModel
):
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

    enabled: bool = False
    lag_threshold: int | None = None
    polling_interval: int | None = None
    cooldown_period: int | None = None
    offset_reset_policy: str | None = None
    min_replicas: int | None = Field(
        default=None,
        title="Min replica count",
    )
    max_replicas: int | None = Field(
        default=None,
        title="Max replica count",
    )
    idle_replicas: int | None = Field(
        default=None,
        title="Idle replica count",
    )
    internal_topics: SerializeAsOptional[list[str]] = []
    topics: SerializeAsOptional[list[str]] = []
    additional_triggers: SerializeAsOptional[list[str]] = []

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")


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


class JmxRuleType(StrEnum):
    GAUGE = "GAUGE"
    COUNTER = "COUNTER"
    UNTYPED = "UNTYPED"


class JMXRule(SerializeAsOptionalModel, CamelCaseConfigModel, DescConfigModel):
    """JMX rule.

    :param pattern: Regex pattern to match against each bean attribute. The pattern is not anchored. Capture groups can be used in other options. Defaults to matching everything.
    :param name: The metric name to set. Capture groups from the pattern can be used. If not specified, the default format will be used. If it evaluates to empty, processing of this attribute stops with no output. An Additional suffix may be added to this name (e.g _total for type COUNTER)
    :param value: Value for the metric. Static values and capture groups from the pattern can be used. If not specified the scraped mBean value will be used.
    :param value_factor: Optional number that value (or the scraped mBean value if value is not specified) is multiplied by, mainly used to convert mBean values from milliseconds to seconds.
    :param help: Help text for the metric. Capture groups from pattern can be used. name must be set to use this. Defaults to the mBean attribute description, domain, and name of the attribute.
    :param attr_name_snake_case: Converts the attribute name to snake case. This is seen in the names matched by the pattern and the default format. For example, anAttrName to an_attr_name.
    :param cache: Whether to cache bean name expressions to rule computation (match and mismatch). Not recommended for rules matching on bean value, as only the value from the first scrape will be cached and re-used. This can increase performance when collecting a lot of mbeans.
    :param type: The type of the metric. name must be set to use this.
    :param labels: A map of label name to label value pairs. Capture groups from pattern can be used in each. name must be set to use this. Empty names and values are ignored. If not specified and the default format is not being used, no labels are set.
    """

    pattern: str | None = None
    name: str | None = None
    value: str | bool | int | float | None = None
    value_factor: float | None = None
    help: str | None = None
    attr_name_snake_case: bool | None = None
    cache: bool | None = None
    type: JmxRuleType | None = None
    labels: SerializeAsOptional[dict[str, str]] = {}


class PrometheusExporterConfig(CamelCaseConfigModel, DescConfigModel):
    """Prometheus JMX exporter configuration.

    :param jmx: The prometheus JMX exporter configuration.

    """

    class PrometheusJMXExporterConfig(
        SerializeAsOptionalModel, CamelCaseConfigModel, DescConfigModel
    ):
        """Prometheus JMX exporter configuration.

        :param enabled: Whether to install Prometheus JMX Exporter as a sidecar container and expose JMX metrics to Prometheus.
        :param image: Docker Image for Prometheus JMX Exporter container.
        :param image_tag: Docker Image Tag for Prometheus JMX Exporter container.
        :param image_pull_policy: Docker Image Pull Policy for Prometheus JMX Exporter container.
        :param port: JMX Exporter Port which exposes metrics in Prometheus format for scraping.
        :param resources: JMX Exporter resources configuration.
        :param metric_rules: List of JMX metric rules.
        """

        enabled: bool | None = None
        image: str | None = None
        image_tag: str | None = None
        image_pull_policy: ImagePullPolicy | None = None
        port: int | None = None
        resources: Resources | None = None
        metric_rules: SerializeAsOptional[list[JMXRule]] = []

    jmx: PrometheusJMXExporterConfig | None = None


class JMXConfig(CamelCaseConfigModel, DescConfigModel):
    """JMX configuration options.

    :param enabled: Whether or not to open JMX port for remote access (e.g., for debugging)
    :param host: The host to use for JMX remote access.
    :param port: The JMX port which JMX style metrics are exposed.
    """

    enabled: bool | None = None
    host: str | None = None
    port: int | None = None


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

    kafka: StreamsConfig = StreamsConfig()  # pyright: ignore[reportIncompatibleVariableOverride]
    autoscaling: StreamsAppAutoScaling | None = None
    stateful_set: bool = False
    persistence: PersistenceConfig | None = None
    prometheus: PrometheusExporterConfig | None = None
    jmx: JMXConfig | None = None
    termination_grace_period_seconds: int | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
