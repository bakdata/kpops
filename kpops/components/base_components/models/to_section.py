from enum import Enum
from typing import Any

from pydantic import BaseConfig, BaseModel, Extra, Field, root_validator


class OutputTopicTypes(str, Enum):
    """Types of output topic

    error (error topic), output (output topic), and extra topics. Every extra topic must have a role.
    """

    ERROR = "error"
    OUTPUT = "output"
    EXTRA = "extra"


class TopicConfig(BaseModel):
    """Configures a topic"""

    type: OutputTopicTypes = Field(..., description="Topic type")
    key_schema: str | None = Field(
        default=None, alias="keySchema", description="Key schema class name"
    )
    value_schema: str | None = Field(
        default=None, alias="valueSchema", description="Value schema class name"
    )
    partitions_count: int | None = Field(
        default=None, description="Number of partitions"
    )
    replication_factor: int | None = Field(
        default=None, description="Replication factor"
    )
    configs: dict[str, str] = Field(default={}, description="Topic configs")
    role: str | None = Field(default=None, description="Topic role")

    class Config(BaseConfig):
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
    """Holds multiple output topics"""
    
    models: dict[
        str, Any
    ] = (
        {}
    )  # any because snapshot versions must be supported  # TODO: really multiple models?
    topics: dict[str, TopicConfig] = Field(..., description="Output topics")

    class Config(BaseConfig):
        extra = Extra.allow
