from dataclasses import dataclass, field

from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)


@dataclass(kw_only=True)
class ProducerStreamsConfig(KafkaStreamsConfig):
    output_topic: str | None = None
    extra_output_topics: dict[str, str] = field(default_factory=dict)


@dataclass(kw_only=True)
class ProducerValues(KafkaAppConfig):
    streams: ProducerStreamsConfig

    # TODO: allow extra
