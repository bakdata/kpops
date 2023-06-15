from enum import Enum
from typing import NewType

from pydantic import BaseModel, Extra, Field, root_validator

from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfig


class InputTopicTypes(str, Enum):
    """Input topic types

    input (input topic), input_pattern (input pattern topic), extra (extra topic), extra_pattern (extra pattern topic).
    Every extra topic must have a role.
    """

    INPUT = "input"
    PATTERN = "pattern"


class FromTopic(BaseModel):
    """Input topic

    :param type: Topic type, defaults to None
    :type type: InputTopicTypes | None, optional
    :param role: Custom identifier belonging to a topic, provide only if `type` is `extra` or `extra-pattern`.
        When `role` is defined, `type: pattern` is equal to `type: extra-pattern`, defaults to None
    :type role: str | None, optional
    """

    type: InputTopicTypes | None = Field(
        default=None, description=describe_attr("type", __doc__)
    )
    role: str | None = Field(default=None, description=describe_attr("role", __doc__))

    class Config(DescConfig):
        extra = Extra.forbid
        use_enum_values = True

    @root_validator
    def extra_topic_role(cls, values: dict) -> dict:
        """Ensure that cls.role is used correctly, assign type if needed"""
        has_role = bool(values["role"])
        match values["type"], has_role:
            case None, False:
                values["type"] = InputTopicTypes.INPUT
                return values
            case InputTopicTypes.INPUT, True:
                raise ValueError(
                    "`type: input` requires `role: null`. Definition of `role` can be omitted in this case."
                )
        return values


TopicName = NewType("TopicName", str)
ComponentName = NewType("ComponentName", str)


class FromSection(BaseModel):
    """Holds multiple input topics

    :param topics: Input topics
    :type topics: dict[str, FromTopic]
    :param components: Components to read from
    :type components: dict[ComponentName, FromTopic]
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
