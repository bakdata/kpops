from enum import Enum
from typing import Any

from pydantic import BaseModel, Extra, Field, root_validator

from kpops.components.base_components.models import TopicName
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfig, DescConfig


class OutputTopicTypes(str, Enum):
    """Types of output topic

    Error (error topic), output (output topic), and extra topics. Every extra topic must have a role.
    """

    ERROR = "error"
    OUTPUT = "output"
    EXTRA = "extra"


class TopicConfig(BaseModel):
    """Configure an output topic

    :param type: Topic type
    :type type: InputTopicTypes
    :param key_schema: Key schema class name
    :type key_schema: str | None
    :param value_schema: Value schema class name
    :type value_schema: str | None
    :param partitions_count: Number of partitions into which the topic is divided
    :type partitions_count: int | None
    :param replication_factor: Replication topic of the topic
    :type replication_factor: int | None
    :param configs: Topic configs
    :type configs: dict[str, str | int]
    :param role: Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`
    :type role: str | None
    """

    type: OutputTopicTypes = Field(..., description=describe_attr("type", __doc__))
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
    role: str | None = Field(
        default=None,
        description=describe_attr("role", __doc__),
    )

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.forbid
        allow_population_by_field_name = True
        use_enum_values = True

    @root_validator
    def extra_topic_role(cls, values):
        """Ensure that cls.role is used correctly"""
        is_extra_topic: bool = values["type"] == OutputTopicTypes.EXTRA
        if is_extra_topic and not values.get("role"):
            raise ValueError(
                "If you define an extra output topic, you have to define a role."
            )
        if not is_extra_topic and values.get("role"):
            raise ValueError(
                "If you do not define a output topic, the role is unnecessary. (This topic is either an output topic "
                "without a role or an error topic)"
            )
        return values


class ToSection(BaseModel):
    """Holds multiple output topics

    :param models: Data models
    :type models: dict[str, Any]
    :param topics: Output topics
    :type topics: dict[str, TopicConfig]
    """

    # TODO: really multiple models?
    # any because snapshot versions must be supported
    models: dict[str, Any] = Field(
        default={}, description=describe_attr("models", __doc__)
    )
    topics: dict[TopicName, TopicConfig] = Field(
        ..., description=describe_attr("topics", __doc__)
    )

    class Config(DescConfig):
        extra = Extra.allow
