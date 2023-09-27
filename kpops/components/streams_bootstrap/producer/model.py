from pydantic import BaseConfig, Extra, Field

from kpops.components.base_components.kafka_app import (
    KafkaAppConfig,
    KafkaStreamsConfig,
)
from kpops.utils.docstring import describe_attr


class ProducerStreamsConfig(KafkaStreamsConfig):
    """Kafka Streams settings specific to Producer.

    :param extra_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    extra_output_topics: dict[str, str] = Field(
        default={}, description=describe_attr("extra_output_topics", __doc__)
    )
    output_topic: str | None = Field(
        default=None, description=describe_attr("output_topic", __doc__)
    )


class ProducerValues(KafkaAppConfig):
    """Settings specific to producers.

    :param streams: Kafka Streams settings
    """

    streams: ProducerStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )

    class Config(BaseConfig):
        extra = Extra.allow
