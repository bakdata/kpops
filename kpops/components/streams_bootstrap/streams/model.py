from collections.abc import Mapping, Set
from typing import Any

from pydantic import BaseConfig, BaseModel, Extra, Field
from typing_extensions import override

from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfig, DescConfig


class StreamsConfig(KafkaStreamsConfig):
    """Streams Bootstrap streams section.

    :param input_topics: Input topics, defaults to []
    :param input_pattern: Input pattern, defaults to None
    :param extra_input_topics: Extra input topics, defaults to {}
    :param extra_input_patterns: Extra input patterns, defaults to {}
    :param extra_output_topics: Extra output topics, defaults to {}
    :param output_topic: Output topic, defaults to None
    :param error_topic: Error topic, defaults to None
    :param config: Configuration, defaults to {}
    """

    input_topics: list[str] = Field(
        default=[], description=describe_attr("input_topics", __doc__)
    )
    input_pattern: str | None = Field(
        default=None, description=describe_attr("input_pattern", __doc__)
    )
    extra_input_topics: dict[str, list[str]] = Field(
        default={}, description=describe_attr("extra_input_topics", __doc__)
    )
    extra_input_patterns: dict[str, str] = Field(
        default={}, description=describe_attr("extra_input_patterns", __doc__)
    )
    extra_output_topics: dict[str, str] = Field(
        default={}, description=describe_attr("extra_output_topics", __doc__)
    )
    output_topic: str | None = Field(
        default=None, description=describe_attr("output_topic", __doc__)
    )
    error_topic: str | None = Field(
        default=None, description=describe_attr("error_topic", __doc__)
    )
    config: dict[str, str] = Field(
        default={}, description=describe_attr("config", __doc__)
    )

    def add_input_topics(self, topics: list[str]) -> None:
        """Add given topics to the list of input topics.

        Ensures no duplicate topics in the list.

        :param topics: Input topics
        """
        self.input_topics = deduplicate(self.input_topics + topics)

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        """Add given extra topics that share a role to the list of extra input topics.

        Ensures no duplicate topics in the list.

        :param topics: Extra input topics
        :param role: Topic role
        """
        self.extra_input_topics[role] = deduplicate(
            self.extra_input_topics.get(role, []) + topics
        )

    @override
    def dict(
        self,
        *,
        include: None | Set[int | str] | Mapping[int | str, Any] = None,
        exclude: None | Set[int | str] | Mapping[int | str, Any] = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        **kwargs,
    ) -> dict:
        """Generate a dictionary representation of the model.

        Optionally, specify which fields to include or exclude.

        :param include: Fields to include
        :param include: Fields to exclude
        :param by_alias: Use the fields' aliases in the dictionary
        :param skip_defaults: Whether to skip defaults
        :param exclude_unset: Whether to exclude unset fields
        """
        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            # The following lines are required only for the streams configs since we never not want to export defaults here, just fallback to helm default values
            exclude_defaults=True,
            exclude_none=True,
        )


class StreamsAppAutoScaling(BaseModel):
    """Kubernetes Event-driven Autoscaling config.

    :param enabled: Whether to enable auto-scaling using KEDA., defaults to False
    :param consumer_group: Name of the consumer group used for checking the
        offset on the topic and processing the related lag.
    :param lag_threshold: Average target value to trigger scaling actions.
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
    consumer_group: str = Field(
        title="Consumer group",
        description=describe_attr("consumer_group", __doc__),
    )
    lag_threshold: int = Field(
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

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.allow


class StreamsAppConfig(KafkaAppConfig):
    """StreamsBoostrap app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.

    :param streams: Streams Bootstrap streams section
    :param autoscaling: Kubernetes Event-driven Autoscaling config, defaults to None
    """

    streams: StreamsConfig = Field(
        default=...,
        description=describe_attr("streams", __doc__),
    )
    autoscaling: StreamsAppAutoScaling | None = Field(
        default=None,
        description=describe_attr("autoscaling", __doc__),
    )

    class Config(BaseConfig):
        extra = Extra.allow
