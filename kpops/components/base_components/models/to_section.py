from enum import Enum
from typing import Any

from pydantic import BaseModel, Extra, Field, root_validator

from kpops.components.base_components.models import TopicName
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfig


class OutputTopicTypes(str, Enum):
    """Types of output topic

    OUTPUT (output topic), ERROR (error topic)
    """

    OUTPUT = "output"
    ERROR = "error"


class TopicConfig(BaseModel):
    """Configure an output topic

    :param type: Topic type, defaults to None
    :param key_schema: Key schema class name, defaults to None
    :param partitions_count: Number of partitions into which the topic is divided,
        defaults to None
    :param replication_factor: Replication topic of the topic, defaults to None
    :param configs: Topic configs, defaults to {}
    :param role: Custom identifier belonging to one or multiple topics, define
        only if `type` is undefined, defaults to None
    """

    type: OutputTopicTypes | None = Field(
        default=None, description=describe_attr("type", __doc__)
    )
    key_schema: str | None = Field(
        default=None,
        alias="keySchema",
        description=describe_attr("key_schema", __doc__),
    )
    value_schema: str | None = Field(
        default=None,
        alias="valueSchema",
        description=describe_attr("value_schema", __doc__),
    )
    partitions_count: int | None = Field(
        default=None, description=describe_attr("partitions_count", __doc__)
    )
    replication_factor: int | None = Field(
        default=None, description=describe_attr("replication_factor", __doc__)
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
    def extra_topic_role(cls, values):
        """Ensure that cls.role is used correctly, assign type if needed"""
        match bool(values["type"]), bool(values["role"]):
            case False, False:
                values["type"] = OutputTopicTypes.OUTPUT
                return values
            case True, True:
                raise ValueError("Define `role` only if `type` is undefined")
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
