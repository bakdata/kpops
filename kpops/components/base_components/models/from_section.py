from enum import Enum
from typing import Any, NewType

from pydantic import BaseModel, Extra, Field, root_validator

from kpops.components.base_components.models import TopicName
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfig


class InputTopicTypes(str, Enum):
    """Input topic types.

    INPUT (input topic), PATTERN (extra-topic-pattern or input-topic-pattern)
    """

    INPUT = "input"
    PATTERN = "pattern"


class FromTopic(BaseModel):
    """Input topic.

    :param type: Topic type, defaults to None
    :param role: Custom identifier belonging to a topic;
        define only if `type` is `pattern` or `None`, defaults to None
    """

    type: InputTopicTypes | None = Field(
        default=None, description=describe_attr("type", __doc__)
    )
    role: str | None = Field(default=None, description=describe_attr("role", __doc__))

    class Config(DescConfig):
        extra = Extra.forbid
        use_enum_values = True

    @root_validator
    def extra_topic_role(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Ensure that cls.role is used correctly, assign type if needed."""
        if values["type"] == InputTopicTypes.INPUT and values["role"]:
            msg = "Define role only if `type` is `pattern` or `None`"
            raise ValueError(msg)
        return values


ComponentName = NewType("ComponentName", str)


class FromSection(BaseModel):
    """Holds multiple input topics.

    :param topics: Input topics
    :param components: Components to read from
    """

    topics: dict[TopicName, FromTopic] = Field(
        default={},
        description=describe_attr("topics", __doc__),
    )
    components: dict[ComponentName, FromTopic] = Field(
        default={},
        description=describe_attr("components", __doc__),
    )

    class Config(DescConfig):
        extra = Extra.forbid
