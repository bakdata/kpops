from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)


class ProducerStreamsConfig(KafkaStreamsConfig):
    output_topic: str | None = None
    extra_output_topics: dict[str, str] = {}


class ProducerValues(KafkaAppConfig):
    streams: ProducerStreamsConfig

    # TODO: allow extra
