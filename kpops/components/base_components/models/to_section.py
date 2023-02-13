from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from apischema import alias


class OutputTopicTypes(str, Enum):
    """Types of output topic.
    error (error topic), output (output topic), and extra topics. Every extra topic must have a role.
    """

    ERROR = "error"
    OUTPUT = "output"
    EXTRA = "extra"


@dataclass(kw_only=True)
class TopicConfig:
    """Configures a topic"""

    type: OutputTopicTypes
    key_schema: str | None = field(default=None, metadata=alias("keySchema"))
    value_schema: str | None = field(default=None, metadata=alias("valueSchema"))
    partitions_count: int | None = None
    replication_factor: int | None = None
    configs: dict[str, str] = field(default_factory=dict)
    role: str | None = None

    # @root_validator # TODO
    # def extra_topic_role(cls, values):
    #     is_extra_topic: bool = values["type"] == OutputTopicTypes.EXTRA
    #     if is_extra_topic and not values.get("role"):
    #         raise ValueError(
    #             "If you define an extra output topic, you have to define a role."
    #         )
    #     if not is_extra_topic and values.get("role"):
    #         raise ValueError(
    #             "If you do not define a output topic, the role is unnecessary. (This topic is either an output topic "
    #             "without a role or an error topic)"
    #         )
    #     return values


@dataclass(kw_only=True)
class ToSection:
    topics: dict[str, TopicConfig]
    models: dict[str, Any] = field(
        default_factory=dict
    )  # any because snapshot versions must be supported  # TODO: really multiple models?

    # TODO: allow extra
