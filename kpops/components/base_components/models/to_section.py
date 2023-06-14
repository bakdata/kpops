from enum import Enum
from typing import Any

from pydantic import BaseModel, Extra, Field, root_validator

from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfig


class OutputTopicTypes(str, Enum):
    """Types of output topic

    Error (error topic), output (output topic), and extra topics. Every extra topic must have a role.
    """

    ERROR = "error"
    OUTPUT = "output"
    EXTRA = "extra"


class TopicConfig(BaseModel):
    """Configure an output topic

    :param type: Topic type, defaults to None
    :type type: InputTopicType | None, optional
    :param key_schema: Key schema class name, defaults to None
    :type key_schema: str | None, optional
    :param partitions_count: Number of partitions into which the topic is divided,
        defaults to None
    :type partitions_count: int | None, optional
    :param replication_factor: Replication topic of the topic, defaults to None
    :type replication_factor: int | None, optional
    :param configs: Topic configs, defaults to {}
    :type configs: dict[str, str | int], optional
    :param role: Custom identifier belonging to one or multiple topics, provide
        only if `type` is `extra`, defaults to None
    :type role: str | None, optional
    """

    type: OutputTopicTypes | None = Field(default=None, description="Topic type")
    key_schema: str | None = Field(
        default=None, alias="keySchema", description="Key schema class name"
    )
    value_schema: str | None = Field(
        default=None, alias="valueSchema", description="Value schema class name"
    )
    partitions_count: int | None = Field(
        default=None, description="Number of partitions into which the topic is divided"
    )
    replication_factor: int | None = Field(
        default=None, description="Replication topic of the topic"
    )
    configs: dict[str, str | int] = Field(default={}, description="Topic configs")
    role: str | None = Field(
        default=None,
        description="Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
    )

    class Config(DescConfig):
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

    def __init__(
        self, type: OutputTopicTypes | None = None, role: str | None = None, **kwargs
    ):
        type = self.__assign_type(type, role)
        super().__init__(type=type, role=role, **kwargs)

    @staticmethod
    def __assign_type(
        type_: OutputTopicTypes | None, role: str | None
    ) -> OutputTopicTypes:
        if type_ is None:
            if role is None:
                type_ = OutputTopicTypes.OUTPUT
            else:
                type_ = OutputTopicTypes.EXTRA
        return type_


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
    topics: dict[str, TopicConfig] = Field(
        ..., description=describe_attr("topics", __doc__)
    )

    class Config(DescConfig):
        extra = Extra.allow
