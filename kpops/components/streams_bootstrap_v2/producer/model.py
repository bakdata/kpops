from typing import ClassVar

from pydantic import ConfigDict

from kpops.components.streams_bootstrap_v2.base import (
    KafkaStreamsConfig,
    StreamsBootstrapV2Values,
)


class ProducerStreamsConfig(KafkaStreamsConfig):
    """Kafka Streams settings specific to Producer."""


class ProducerAppV2Values(StreamsBootstrapV2Values):
    """Settings specific to producers.

    :param streams: Kafka Streams settings
    """

    streams: ProducerStreamsConfig  # pyright: ignore[reportIncompatibleVariableOverride]

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
