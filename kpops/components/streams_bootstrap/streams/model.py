from typing import AbstractSet, Any, Mapping
from typing_extensions import override

from pydantic import BaseConfig, BaseModel, Extra, Field

from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)
from kpops.utils.pydantic import CamelCaseConfig


class StreamsConfig(KafkaStreamsConfig):
    """Streams Bootstrap streams section"""

    input_topics: list[str] = []
    input_pattern: str | None = None
    extra_input_topics: dict[str, list[str]] = {}
    extra_input_patterns: dict[str, str] = {}
    extra_output_topics: dict[str, str] = {}
    output_topic: str | None = None
    error_topic: str | None = None
    config: dict[str, str] = {}

    def add_input_topics(self, topics: list[str]) -> None:
        """Add given topics to the list of input topics.

        Ensures no duplicate topics in the list.

        :param topics: Input topics
        :type topics: list[str]
        """
        self.input_topics = deduplicate(self.input_topics + topics)

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        """Add given extra topics that share a role to the list of extra input topics.

        Ensures no duplicate topics in the list.

        :param topics: Extra input topics
        :type topics: list[str]
        :param role: Topic role
        :type role: str
        """
        self.extra_input_topics[role] = deduplicate(
            self.extra_input_topics.get(role, []) + topics
        )

    @override
    def dict(
        self,
        *,
        include: None | AbstractSet[int | str] | Mapping[int | str, Any] = None,
        exclude: None | AbstractSet[int | str] | Mapping[int | str, Any] = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        **kwargs,
    ) -> dict:
        """Generate a dictionary representation of the model

        Optionally, specify which fields to include or exclude.

        :param include: Fields to include
        :type include: None | AbstractSet[int | str] | Mapping[int | str, Any]
        :param include: Fields to exclude
        :type include: None | AbstractSet[int | str] | Mapping[int | str, Any]
        :param by_alias: Use the fields' aliases in the dictionary
        :type by_alias: bool
        :param skip_defaults: Whether to skip defaults
        :type skip_defaults: bool | None
        :param exclude_unset: Whether to exclude unset fields
        :type exclude_unset: bool
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
    enabled: bool = Field(
        default=False, description="Whether to enable auto-scaling using KEDA."
    )
    consumer_group: str = Field(
        title="Consumer group",
        description="Name of the consumer group used for checking the offset on the topic and processing the related lag.",
    )
    lag_threshold: int = Field(
        title="Lag threshold",
        description="Average target value to trigger scaling actions.",
    )
    polling_interval: int = Field(
        default=30,
        title="Polling interval",
        description=(
            "This is the interval to check each trigger on. "
            "https://keda.sh/docs/2.9/concepts/scaling-deployments/#pollinginterval"
        ),
    )
    cooldown_period: int = Field(
        default=300,
        title="Cooldown period",
        description=(
            "The period to wait after the last trigger reported active before scaling the resource back to 0. "
            "https://keda.sh/docs/2.9/concepts/scaling-deployments/#cooldownperiod"
        ),
    )
    offset_reset_policy: str = Field(
        default="earliest",
        title="Offset reset policy",
        description="The offset reset policy for the consumer if the the consumer group is not yet subscribed to a partition.",
    )
    min_replicas: int = Field(
        default=0,
        title="Min replica count",
        description=(
            "Minimum number of replicas KEDA will scale the resource down to. "
            "https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount"
        ),
    )
    max_replicas: int = Field(
        default=1,
        title="Max replica count",
        description=(
            "This setting is passed to the HPA definition that KEDA will create for a given resource and holds the maximum number of replicas of the target resouce. "
            "https://keda.sh/docs/2.9/concepts/scaling-deployments/#maxreplicacount"
        ),
    )
    idle_replicas: int | None = Field(
        default=None,
        title="Idle replica count",
        description=(
            "If this property is set, KEDA will scale the resource down to this number of replicas. "
            "https://keda.sh/docs/2.9/concepts/scaling-deployments/#idlereplicacount"
        ),
    )
    topics: list[str] = Field(
        default=[],
        description="List of auto-generated Kafka Streams topics used by the streams app.",
    )

    class Config(CamelCaseConfig):
        extra = Extra.allow


class StreamsAppConfig(KafkaAppConfig):
    """
    StreamsBoostrap app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.
    """

    streams: StreamsConfig
    autoscaling: StreamsAppAutoScaling | None = None

    class Config(BaseConfig):
        extra = Extra.allow
