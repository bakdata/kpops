from enum import Enum
from typing import Any

from pydantic import BaseConfig, BaseModel, Extra, Field, root_validator


class OutputTopicTypes(str, Enum):
    """
    Types of output topic
    error (error topic), output (output topic), and extra topics. Every extra topic must have a role.
    """

    ERROR = "error"
    OUTPUT = "output"
    EXTRA = "extra"


class TopicConfig(BaseModel):
    """Configures a topic"""

    type: OutputTopicTypes = Field(...)
    key_schema: str | None = Field(default=None, alias="keySchema")
    value_schema: str | None = Field(default=None, alias="valueSchema")
    partitions_count: int | None = None
    replication_factor: int | None = None
    configs: dict[str, str] = {}
    role: str | None = None

    class Config(BaseConfig):
        extra = Extra.forbid
        use_enum_values = True

    @root_validator
    def extra_topic_role(cls, values):
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
    models: dict[
        str, Any
    ] = (
        {}
    )  # any because snapshot versions must be supported  # TODO: really multiple models?
    topics: dict[str, TopicConfig]

    class Config(BaseConfig):
        extra = Extra.allow
