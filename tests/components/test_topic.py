import re
from collections.abc import Iterable
from typing import ClassVar

import pydantic
import pytest

from kpops.components.common.topic import (
    KafkaTopic,
    KafkaTopicStr,
    OutputTopicTypes,
    TopicConfig,
)


class Model(pydantic.BaseModel):
    __test__: ClassVar[bool] = False
    topic: KafkaTopicStr | None


class TestKafkaTopic:
    def test_id(self) -> None:
        topic = KafkaTopic(name="foo")
        assert topic.id == "topic-foo"

    def test_kafka_topic_str(self) -> None:
        model = Model(topic=None)
        assert model.topic is None
        assert model.model_dump()["topic"] is None

        model = Model(topic="topic-name")  # ty: ignore[invalid-argument-type]
        assert model.topic == KafkaTopic(name="topic-name")
        assert model.model_dump()["topic"] == "topic-name"

        exc_msg = "Topic should be a valid KafkaTopic instance or topic name string"
        with pytest.raises(pydantic.ValidationError, match=re.escape(exc_msg)):
            Model(topic="")  # ty: ignore[invalid-argument-type]

        with pytest.raises(pydantic.ValidationError, match=re.escape(exc_msg)):
            Model(topic=1)  # ty: ignore[invalid-argument-type]

    @pytest.mark.parametrize(
        ("input", "expected"),
        [
            pytest.param(
                [KafkaTopic(name="a")],
                [KafkaTopic(name="a")],
                id="single element",
            ),
            pytest.param(
                [KafkaTopic(name="a"), KafkaTopic(name="a")],
                [KafkaTopic(name="a")],
                id="repetition single",
            ),
            pytest.param(
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
                id="no repetition",
            ),
            pytest.param(
                [KafkaTopic(name="a"), KafkaTopic(name="b"), KafkaTopic(name="a")],
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
                id="repetition multiple",
            ),
            pytest.param(
                [
                    KafkaTopic(name="a"),
                    KafkaTopic(name="a"),
                    KafkaTopic(name="b"),
                    KafkaTopic(name="b"),
                    KafkaTopic(name="a"),
                    KafkaTopic(name="b"),
                ],
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
                id="repetition complex",
            ),
            pytest.param(
                [
                    KafkaTopic(
                        name="a", config=TopicConfig(type=OutputTopicTypes.OUTPUT)
                    ),
                    KafkaTopic(name="b"),
                    KafkaTopic(
                        name="a", config=TopicConfig(type=OutputTopicTypes.ERROR)
                    ),
                ],
                [
                    KafkaTopic(
                        name="a", config=TopicConfig(type=OutputTopicTypes.ERROR)
                    ),
                    KafkaTopic(name="b"),
                ],
                id="overwrite",
            ),
        ],
    )
    def test_deduplicate(
        self, input: Iterable[KafkaTopic], expected: list[KafkaTopic]
    ) -> None:
        assert KafkaTopic.deduplicate(input) == expected
