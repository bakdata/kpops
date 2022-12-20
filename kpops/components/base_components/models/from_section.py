from enum import Enum

from pydantic import BaseConfig, BaseModel, Extra, Field, root_validator


class InputTopicTypes(str, Enum):
    INPUT = "input"
    EXTRA = "extra"
    INPUT_PATTERN = "input-pattern"
    EXTRA_PATTERN = "extra-pattern"


class FromTopic(BaseModel):
    type: InputTopicTypes = Field(...)
    role: str | None = None

    class Config(BaseConfig):
        extra = Extra.forbid
        use_enum_values = True

    @root_validator
    def extra_topic_role(cls, values):
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
    topics: dict[str, FromTopic]

    class Config(BaseConfig):
        extra = Extra.forbid
