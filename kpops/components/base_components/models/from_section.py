from enum import StrEnum
from typing import Any, ClassVar, NewType

from pydantic import ConfigDict, model_validator

from kpops.components.base_components.models import TopicName
from kpops.utils.pydantic import DescConfigModel


class InputTopicTypes(StrEnum):
    """Input topic types.

    - INPUT: input topic
    - PATTERN: extra-topic-pattern or input-topic-pattern
    """

    INPUT = "input"
    PATTERN = "pattern"


class FromTopic(DescConfigModel):
    """Input topic.

    :param type: Topic type, defaults to None
    :param label: Custom identifier belonging to a topic;
        define only if `type` is `pattern` or `None`, defaults to None
    """

    type: InputTopicTypes | None = None
    label: str | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        use_enum_values=True,
    )

    @model_validator(mode="after")
    def extra_topic_label(self) -> Any:
        """Ensure that `cls.label` is used correctly, assign type if needed."""
        if self.type == InputTopicTypes.INPUT and self.label:
            msg = "Define label only if `type` is `pattern` or `None`"
            raise ValueError(msg)
        return self


ComponentName = NewType("ComponentName", str)


class FromSection(DescConfigModel):
    """Holds multiple input topics.

    :param topics: Input topics
    :param components: Components to read from
    """

    topics: dict[TopicName, FromTopic] = {}
    components: dict[ComponentName, FromTopic] = {}

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
