from enum import Enum

from pydantic import BaseConfig, BaseModel, Extra, Field, root_validator


class InputTopicTypes(str, Enum):
    """Input topic types

    input (input topic), input_pattern (input pattern topic), extra (extra topic), extra_pattern (extra pattern topic).
    Every extra topic must have a role.
    """

    INPUT = "input"
    EXTRA = "extra"
    INPUT_PATTERN = "input-pattern"
    EXTRA_PATTERN = "extra-pattern"


class FromTopic(BaseModel):
    """Input topic

    :param type: Topic type
    :type type: InputTopicTypes
    :param role: Custom identifier belonging to a topic, provide only if `type` is `extra` or `extra-pattern`
    :type role: str | None
    """

    type: InputTopicTypes = Field(..., description="Topic type")
    role: str | None = Field(
        default=None,
        description="Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
    )

    class Config(BaseConfig):
        extra = Extra.forbid
        use_enum_values = True

    @root_validator
    def extra_topic_role(cls, values):
        """Ensure that cls.role is used correctly"""
        is_extra_topic = values["type"] in (
            InputTopicTypes.EXTRA,
            InputTopicTypes.EXTRA_PATTERN,
        )
        if is_extra_topic and not values.get("role"):
            raise ValueError(
                "If you define an extra input topic or extra input pattern, you have to define a role."
            )
        if not is_extra_topic and values.get("role"):
            raise ValueError(
                "If you do not define an input topic or input pattern, the role is unnecessary."
            )
        return values


class FromSection(BaseModel):
    """Holds multiple input topics

    :param topics: Input topics
    :type topics: dict[str, FromTopic]
    """

    topics: dict[str, FromTopic] = Field(..., description="Input topics")

    class Config(BaseConfig):
        extra = Extra.forbid
