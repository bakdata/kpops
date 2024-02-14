from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from typing import Annotated, Any

import pydantic
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfigModel


class OutputTopicTypes(str, Enum):
    """Types of output topic.

    - OUTPUT: output topic
    - ERROR: error topic
    """

    OUTPUT = "output"
    ERROR = "error"


class TopicConfig(DescConfigModel):
    """Configure an output topic.

    :param type: Topic type
    :param key_schema: Key schema class name
    :param value_schema: Value schema class name
    :param partitions_count: Number of partitions into which the topic is divided
    :param replication_factor: Replication factor of the topic
    :param configs: Topic configs
    :param role: Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`
    """

    type: OutputTopicTypes | None = Field(
        default=None, title="Topic type", description=describe_attr("type", __doc__)
    )
    key_schema: str | None = Field(
        default=None,
        title="Key schema",
        description=describe_attr("key_schema", __doc__),
    )
    value_schema: str | None = Field(
        default=None,
        title="Value schema",
        description=describe_attr("value_schema", __doc__),
    )
    partitions_count: int | None = Field(
        default=None,
        title="Partitions count",
        description=describe_attr("partitions_count", __doc__),
    )
    replication_factor: int | None = Field(
        default=None,
        title="Replication factor",
        description=describe_attr("replication_factor", __doc__),
    )
    configs: dict[str, str | int] = Field(
        default={}, description=describe_attr("configs", __doc__)
    )
    role: str | None = Field(default=None, description=describe_attr("role", __doc__))

    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def extra_topic_role(self) -> Any:
        """Ensure that `cls.role` is used correctly, assign type if needed."""
        if self.type and self.role:
            msg = "Define `role` only if `type` is undefined"
            raise ValueError(msg)
        return self


class KafkaTopic(BaseModel):
    """Internal representation of a Kafka topic.

    Users configure topic name and config through the `ToSection` of a `PipelineComponent`

    :param name: Topic name
    :param config: Topic config
    """

    name: str
    config: TopicConfig = TopicConfig()

    @property
    def id(self) -> str:
        """Unique identifier of this topic."""
        return f"topic-{self.name}"

    @staticmethod
    def deduplicate(topics: Iterable[KafkaTopic]) -> list[KafkaTopic]:
        """Deduplicate an iterable of Kafka topics based on their name, overwriting previous ones."""
        return list({topic.name: topic for topic in topics}.values())


def deserialize_kafka_topic_from_str(topic: Any) -> KafkaTopic | dict:
    if topic and isinstance(topic, str):
        return KafkaTopic(name=topic)
    if isinstance(topic, KafkaTopic | dict):
        return topic
    msg = f"Topic should be a valid {KafkaTopic.__name__} instance or topic name string"
    raise ValueError(msg)


def serialize_kafka_topic_to_str(topic: KafkaTopic) -> str:
    return topic.name


# Pydantic type for KafkaTopic that serializes to str, used for generating the correct JSON schema
KafkaTopicStr = Annotated[
    KafkaTopic,
    pydantic.WithJsonSchema({"type": "string"}),
    pydantic.BeforeValidator(deserialize_kafka_topic_from_str),
    pydantic.PlainSerializer(serialize_kafka_topic_to_str),
]
