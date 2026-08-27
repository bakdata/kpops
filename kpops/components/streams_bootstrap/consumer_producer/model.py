from typing import ClassVar

from pydantic import ConfigDict

from kpops.components.common.topic import KafkaTopicStr
from kpops.components.streams_bootstrap.consumer.model import (
    ConsumerAppValues,
    ConsumerConfig,
)


class ConsumerProducerConfig(ConsumerConfig):
    """consumerproducer app kafka section.

    :param error_topic: Error topic, defaults to None
    :param delete_output: Whether the output topics with their associated schemas and the consumer group should be deleted during the cleanup, defaults to None
    """

    error_topic: KafkaTopicStr | None = None
    delete_output: bool | None = None


class ConsumerProducerAppValues(ConsumerAppValues):
    """consumerproducer-app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.

    :param kafka: consumerproducer-app kafka section
    """

    kafka: ConsumerProducerConfig = ConsumerProducerConfig()  # pyright: ignore[reportIncompatibleVariableOverride]

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
