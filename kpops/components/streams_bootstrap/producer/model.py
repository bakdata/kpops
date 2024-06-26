from pydantic import ConfigDict, Field

from kpops.components.base_components.kafka_app import (
    KafkaAppValues,
    KafkaStreamsConfig,
)
from kpops.components.streams_bootstrap import StreamsBootstrapValues
from kpops.utils.docstring import describe_attr


class ProducerStreamsConfig(KafkaStreamsConfig):
    """Kafka Streams settings specific to Producer."""


class ProducerAppValues(StreamsBootstrapValues, KafkaAppValues):
    """Settings specific to producers.

    :param streams: Kafka Streams settings
    """

    streams: ProducerStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )

    model_config = ConfigDict(extra="allow")
