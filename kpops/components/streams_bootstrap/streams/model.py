from dataclasses import dataclass, field

from apischema import serialize

from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)


@dataclass(kw_only=True)
class StreamsConfig(KafkaStreamsConfig):
    """
    Streams Bootstrap streams section
    """

    input_topics: list[str] = field(default_factory=list)
    input_pattern: str | None = None
    extra_input_topics: dict[str, list[str]] = field(default_factory=dict)
    extra_input_patterns: dict[str, str] = field(default_factory=dict)
    extra_output_topics: dict[str, str] = field(default_factory=dict)
    output_topic: str | None = None
    error_topic: str | None = None
    config: dict[str, str] = field(default_factory=dict)

    def add_input_topics(self, topics: list[str]) -> None:
        self.input_topics = deduplicate(self.input_topics + topics)

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        self.extra_input_topics[role] = deduplicate(
            self.extra_input_topics.get(role, []) + topics
        )

    def dict(self) -> dict:
        return serialize(self, exclude_defaults=True, exclude_none=True)


@dataclass(kw_only=True)
class StreamsAppAutoScaling:
    consumergroup: str
    topics: list[str] = field(default_factory=list)

    # TODO: allow extra


class StreamsAppConfig(KafkaAppConfig):
    """
    StreamsBoostrap app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.
    """

    streams: StreamsConfig
    autoscaling: StreamsAppAutoScaling | None = None

    # TODO: allow extra
