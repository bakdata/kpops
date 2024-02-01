from typing import Any

import pydantic
from pydantic import ConfigDict, Field

from kpops.components.base_components.kafka_app import (
    KafkaAppValues,
    KafkaStreamsConfig,
)
from kpops.components.base_components.models.to_section import KafkaTopic
from kpops.utils.docstring import describe_attr


class ProducerStreamsConfig(KafkaStreamsConfig):
    """Kafka Streams settings specific to Producer.

    :param extra_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    extra_output_topics: dict[str, KafkaTopic] = Field(
        default={}, description=describe_attr("extra_output_topics", __doc__)
    )
    output_topic: KafkaTopic | None = Field(
        default=None, description=describe_attr("output_topic", __doc__)
    )

    @pydantic.field_validator("output_topic", mode="before")
    @classmethod
    def validate_output_topic(cls, output_topic: Any) -> KafkaTopic | None:
        if output_topic and isinstance(output_topic, str):
            return KafkaTopic(name=output_topic)
        return None

    @pydantic.field_serializer("output_topic")
    def serialize_topic(self, topic: KafkaTopic | None) -> str | None:
        if not topic:
            return None
        return topic.name

    @pydantic.field_serializer("extra_output_topics")
    def serialize_extra_output_topics(
        self, extra_topics: dict[str, KafkaTopic]
    ) -> dict[str, str]:
        return {role: topic.name for role, topic in extra_topics.items()}


class ProducerAppValues(KafkaAppValues):
    """Settings specific to producers.

    :param streams: Kafka Streams settings
    """

    streams: ProducerStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )

    model_config = ConfigDict(extra="allow")
