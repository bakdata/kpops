from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar, Self

import pydantic
from pydantic import ConfigDict, Field

from kpops.components.common.kubernetes_model import ImagePullPolicy, Resources
from kpops.components.common.topic import KafkaTopic
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


class StreamsAppAutoScaling(
    SerializeAsOptionalModel, CamelCaseConfigModel, DescConfigModel
):
    """Kubernetes Event-driven Autoscaling config.

    :param enabled: Whether to enable auto-scaling using KEDA., defaults to False
    :param lag_threshold: Average target value to trigger scaling actions.
        Mandatory when using chart-generated Kafka lag triggers.
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
    :param triggers: Complete list of KEDA triggers. When set, these replace all
        chart-generated Kafka lag triggers, defaults to []
    :param additional_triggers: List of KEDA triggers appended to the generated
        Kafka lag triggers, see https://keda.sh/docs/latest/scalers/,
        defaults to []
    :param scaling_modifiers: KEDA composite metric configuration. Requires explicit
        triggers, defaults to None
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
    triggers: SerializeAsOptional[list[dict[str, Any]]] = []
    additional_triggers: SerializeAsOptional[list[dict[str, Any]]] = []
    scaling_modifiers: dict[str, Any] | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")


class PersistenceConfig(CamelCaseConfigModel, DescConfigModel):
    """streams-bootstrap persistence configurations.

    :param enabled: Whether to use a persistent volume to store the state of the streams app.
    :param size: The size of the PersistentVolume to allocate to each streams pod in the StatefulSet.
    :param storage_class: Storage class to use for the persistent volume.
    :param volume_attributes_class_name: VolumeAttributesClass to use for the persistent volume.
    """

    enabled: bool = False
    size: str | None = None
    storage_class: str | None = None
    volume_attributes_class_name: str | None = None

    @pydantic.model_validator(mode="after")
    def validate_mandatory_fields_are_set(self) -> Self:
        if self.enabled and self.size is None:
            msg = (
                "If app.persistence.enabled is set to true, "
                "the field app.persistence.size needs to be set."
            )
            raise ValueError(msg)
        return self
