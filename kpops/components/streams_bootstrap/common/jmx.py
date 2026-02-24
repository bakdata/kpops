from enum import StrEnum

from kpops.components.common.kubernetes_model import ImagePullPolicy, Resources
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    SerializeAsOptional,
    SerializeAsOptionalModel,
)


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
