from enum import Enum
from typing import Any, NewType

from pydantic import ConfigDict, Field, model_validator

from kpops.components.base_components.models import TopicName
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfigModel


class InputTopicTypes(str, Enum):
    """Input topic types.

    - INPUT: input topic
    - PATTERN: extra-topic-pattern or input-topic-pattern
    """

    INPUT = "input"
    PATTERN = "pattern"


class FromTopic(DescConfigModel):
    """Input topic.

    :param type: Topic type, defaults to None
    :param role: Custom identifier belonging to a topic;
        define only if `type` is `pattern` or `None`, defaults to None
    """

    type: InputTopicTypes | None = Field(
        default=None, description=describe_attr("type", __doc__)
    )
    role: str | None = Field(default=None, description=describe_attr("role", __doc__))

    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def extra_topic_role(self) -> Any:
        """Ensure that `cls.role` is used correctly, assign type if needed."""
        if self.type == InputTopicTypes.INPUT and self.role:
            msg = "Define role only if `type` is `pattern` or `None`"
            raise ValueError(msg)
        return self


ComponentName = NewType("ComponentName", str)


class FromSection(DescConfigModel):
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

    model_config = ConfigDict(
        extra="forbid",
    )
