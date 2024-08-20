from pydantic import ConfigDict, Field

from kpops.components.streams_bootstrap.model import (
    KafkaConfig,
    StreamsBootstrapValues,
)
from kpops.utils.docstring import describe_attr


class ProducerConfig(KafkaConfig):
    """Kafka Streams settings specific to Producer."""


class ProducerAppValues(StreamsBootstrapValues):
    """Settings specific to producers.

    :param kafka: Kafka Streams settings
    """

    kafka: ProducerConfig = Field(description=describe_attr("kafka", __doc__))

    model_config = ConfigDict(extra="allow")
