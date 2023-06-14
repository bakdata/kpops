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
    EXTRA = "extra"
    PATTERN = "pattern"
    INPUT_PATTERN = "input-pattern"
    EXTRA_PATTERN = "extra-pattern"


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
        type_ = values.get("type", None)
        role = values.get("role", None) is not None
        # Assign type
        match type_, role:
            case None, False:
                values["type"] = InputTopicTypes.INPUT
                return values
            case None, True:
                values["type"] = InputTopicTypes.EXTRA
                return values
            case InputTopicTypes.PATTERN, False:
                values["type"] = InputTopicTypes.INPUT_PATTERN
                return values
            case InputTopicTypes.PATTERN, True:
                values["type"] = InputTopicTypes.EXTRA_PATTERN
                return values
            case _, _:
                is_input_topic = values["type"] not in (
                    InputTopicTypes.EXTRA,
                    InputTopicTypes.EXTRA_PATTERN,
                )
        match is_input_topic, role:
            case True, True:
                raise ValueError(
                    "If you define an extra input component, extra input topic, or extra input pattern, you have to define a role."
                )
            case False, False:
                raise ValueError(
                    "If you do not define an extra input component, input topic, or input pattern, the role is unnecessary."
                )
            case _, _:
                return values
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
