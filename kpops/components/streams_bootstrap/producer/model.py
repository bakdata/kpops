from pydantic import BaseConfig, Extra

from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)


class ProducerStreamsConfig(KafkaStreamsConfig):
    extra_output_topics: dict[str, str] = {}
    output_topic: str | None


class ProducerValues(KafkaAppConfig):
    streams: ProducerStreamsConfig

    class Config(BaseConfig):
        extra = Extra.allow
