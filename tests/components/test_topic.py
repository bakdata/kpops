from collections.abc import Iterable

import pytest

from kpops.components.base_components.models.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)


class TestKafkaTopic:
    def test_id(self):
        topic = KafkaTopic(name="foo")
        assert topic.id == "topic-foo"

    @pytest.mark.parametrize(
        ("input", "expected"),
        [
            (
                [KafkaTopic(name="a")],
                [KafkaTopic(name="a")],
            ),
            (
                [KafkaTopic(name="a"), KafkaTopic(name="a")],
                [KafkaTopic(name="a")],
            ),
            (
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
            ),
            (
                [KafkaTopic(name="a"), KafkaTopic(name="b"), KafkaTopic(name="a")],
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
            ),
            (
                [
                    KafkaTopic(name="a"),
                    KafkaTopic(name="a"),
                    KafkaTopic(name="b"),
                    KafkaTopic(name="b"),
                    KafkaTopic(name="a"),
                    KafkaTopic(name="b"),
                ],
                [KafkaTopic(name="a"), KafkaTopic(name="b")],
            ),
            (
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
            ),
        ],
    )
    def test_deduplicate(self, input: Iterable[KafkaTopic], expected: list[KafkaTopic]):
        assert KafkaTopic.deduplicate(input) == expected
