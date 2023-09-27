from enum import Enum
from typing import Any

from pydantic import BaseModel, Extra, Field, root_validator

from kpops.components.base_components.models import ModelName, ModelVersion, TopicName
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfig


class OutputTopicTypes(str, Enum):
    """Types of output topic.

    OUTPUT (output topic), ERROR (error topic)
    """

    OUTPUT = "output"
    ERROR = "error"


class TopicConfig(BaseModel):
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

    class Config(DescConfig):
        extra = Extra.forbid
        allow_population_by_field_name = True
        use_enum_values = True

    @root_validator
    def extra_topic_role(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure that cls.role is used correctly, assign type if needed."""
        if values["type"] and values["role"]:
            msg = "Define `role` only if `type` is undefined"
            raise ValueError(msg)
        return values


class ToSection(BaseModel):
    """Holds multiple output topics.

    :param topics: Output topics
    :param models: Data models
    """

    topics: dict[TopicName, TopicConfig] = Field(
        default={}, description=describe_attr("topics", __doc__)
    )
    models: dict[ModelName, ModelVersion] = Field(
        default={}, description=describe_attr("models", __doc__)
    )

    class Config(DescConfig):
        extra = Extra.allow
