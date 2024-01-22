from pydantic import ConfigDict, Field

from kpops.components.base_components.kafka_app import (
    KafkaAppValues,
    KafkaStreamsConfig,
)
from kpops.components.base_components.models import TopicName, TopicRole
from kpops.utils.docstring import describe_attr


class ProducerStreamsConfig(KafkaStreamsConfig):
    """Kafka Streams settings specific to Producer.

    :param extra_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    extra_output_topics: dict[TopicRole, TopicName] = Field(
        default={}, description=describe_attr("extra_output_topics", __doc__)
    )
    output_topic: TopicName | None = Field(
        default=None, description=describe_attr("output_topic", __doc__)
    )


class ProducerAppValues(KafkaAppValues):
    """Settings specific to producers.

    :param streams: Kafka Streams settings
    """

    streams: ProducerStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )

    model_config = ConfigDict(extra="allow")
