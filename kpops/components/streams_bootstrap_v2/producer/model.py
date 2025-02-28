from typing import ClassVar

from pydantic import ConfigDict, Field

from kpops.components.streams_bootstrap_v2.base import (
    KafkaStreamsConfig,
    StreamsBootstrapV2Values,
)
from kpops.utils.docstring import describe_attr


class ProducerStreamsConfig(KafkaStreamsConfig):
    """Kafka Streams settings specific to Producer."""


class ProducerAppV2Values(StreamsBootstrapV2Values):
    """Settings specific to producers.

    :param streams: Kafka Streams settings
    """

    streams: ProducerStreamsConfig = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        description=describe_attr("streams", __doc__)
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
