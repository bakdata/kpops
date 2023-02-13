from dataclasses import dataclass
from enum import Enum


class InputTopicTypes(str, Enum):
    INPUT = "input"
    EXTRA = "extra"
    INPUT_PATTERN = "input-pattern"
    EXTRA_PATTERN = "extra-pattern"


@dataclass(kw_only=True)
class FromTopic:
    type: InputTopicTypes
    role: str | None = None

    # @root_validator # TODO
    # def extra_topic_role(cls, values):
    #     is_extra_topic = values["type"] in (
    #         InputTopicTypes.EXTRA,
    #         InputTopicTypes.EXTRA_PATTERN,
    #     )
    #     if is_extra_topic and not values.get("role"):
    #         raise ValueError(
    #             "If you define an extra input topic or extra input pattern, you have to define a role."
    #         )
    #     if not is_extra_topic and values.get("role"):
    #         raise ValueError(
    #             "If you do not define an input topic or input pattern, the role is unnecessary."
    #         )
    #     return values


@dataclass(kw_only=True)
class FromSection:
    topics: dict[str, FromTopic]
