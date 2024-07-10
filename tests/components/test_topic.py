from collections.abc import Iterable

import pydantic
import pytest

from kpops.components.common.topic import (
    KafkaTopic,
    KafkaTopicStr,
    OutputTopicTypes,
    TopicConfig,
)


class Model(pydantic.BaseModel):
    __test__ = False
    topic: KafkaTopicStr | None


class TestKafkaTopic:
    def test_id(self):
        topic = KafkaTopic(name="foo")
        assert topic.id == "topic-foo"

    def test_kafka_topic_str(self):
        model = Model(topic=None)
        assert model.topic is None
        assert model.model_dump()["topic"] is None

        model = Model(topic="topic-name")  # pyright: ignore[reportArgumentType]
        assert model.topic == KafkaTopic(name="topic-name")
        assert model.model_dump()["topic"] == "topic-name"

        exc_msg = "Topic should be a valid KafkaTopic instance or topic name string"
        with pytest.raises(ValueError, match=exc_msg):
            Model(topic="")  # pyright: ignore[reportArgumentType]

        with pytest.raises(ValueError, match=exc_msg):
            Model(topic=1)  # pyright: ignore[reportArgumentType]

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
    def test_deduplicate(self, input: Iterable[KafkaTopic], expected: list[KafkaTopic]):
        assert KafkaTopic.deduplicate(input) == expected
