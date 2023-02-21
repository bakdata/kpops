from pydantic import BaseConfig, BaseModel, Extra, Field

from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)
from kpops.utils.pydantic import CamelCaseConfig


class StreamsConfig(KafkaStreamsConfig):
    """
    Streams Bootstrap streams section
    """

    input_topics: list[str] = []
    input_pattern: str | None = None
    extra_input_topics: dict[str, list[str]] = {}
    extra_input_patterns: dict[str, str] = {}
    extra_output_topics: dict[str, str] = {}
    output_topic: str | None = None
    error_topic: str | None = None
    config: dict[str, str] = {}

    def add_input_topics(self, topics: list[str]) -> None:
        self.input_topics = deduplicate(self.input_topics + topics)

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        self.extra_input_topics[role] = deduplicate(
            self.extra_input_topics.get(role, []) + topics
        )

    def dict(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        **kwargs,
    ) -> dict:
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
