from pydantic import ConfigDict, Field

from kpops.components.common.streams_bootstrap import StreamsBootstrapValues
from kpops.components.streams_bootstrap_v3.kafka_app import (
    KafkaAppValues,
    KafkaStreamsConfig,
)
from kpops.utils.docstring import describe_attr


class ProducerStreamsConfig(KafkaStreamsConfig):
    """Kafka Streams settings specific to Producer."""


class ProducerAppValues(StreamsBootstrapValues, KafkaAppValues):
    """Settings specific to producers.

    :param kafka: Kafka Streams settings
    """

    kafka: ProducerStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )

    model_config = ConfigDict(extra="allow")
