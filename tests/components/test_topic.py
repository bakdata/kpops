import re
from collections.abc import Iterable
from typing import ClassVar

import pydantic
import pytest

from kpops.components.common.topic import (
    KafkaTopic,
    KafkaTopicConfigs,
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


class TestTopicConfig:
    @pytest.mark.parametrize(
        ("key", "value", "valid"),
        [
            ("partitions_count", 1, True),
            ("partitions_count", 0, False),
            ("replication_factor", 32767, True),
            ("replication_factor", 0, False),
            ("replication_factor", 32768, False),
        ],
    )
    def test_constraints(self, key: str, value: int, valid: bool) -> None:
        if valid:
            TopicConfig.model_validate({key: value})
        else:
            with pytest.raises(pydantic.ValidationError):
                TopicConfig.model_validate({key: value})


class TestKafkaTopicConfigs:
    @pytest.mark.parametrize(
        ("key", "value", "valid"),
        [
            ("retention.ms", -1, True),
            ("retention.ms", "-1", True),
            ("retention.ms", -2, False),
            ("retention.bytes", -1, True),
            ("retention.bytes", -2, False),
            ("local.retention.ms", -2, True),
            ("local.retention.ms", -3, False),
            ("compression.gzip.level", -1, True),
            ("compression.gzip.level", 9, True),
            ("compression.gzip.level", 0, False),
            ("compression.gzip.level", 10, False),
            ("compression.lz4.level", 17, True),
            ("compression.lz4.level", 18, False),
            ("compression.zstd.level", -131072, True),
            ("compression.zstd.level", 23, False),
            ("min.cleanable.dirty.ratio", 0.5, True),
            ("min.cleanable.dirty.ratio", 1.5, False),
            ("min.insync.replicas", 1, True),
            ("min.insync.replicas", 0, False),
            ("segment.index.bytes", 4, True),
            ("segment.index.bytes", 3, False),
            ("segment.ms", 0, False),
            ("delete.retention.ms", -1, False),
            ("message.timestamp.type", "createtime", False),
        ],
    )
    def test_constraints(self, key: str, value: int | float | str, valid: bool) -> None:
        if valid:
            configs = KafkaTopicConfigs.model_validate({key: value})
            assert configs.model_dump()[key] == str(value)
        else:
            with pytest.raises(pydantic.ValidationError):
                KafkaTopicConfigs.model_validate({key: value})
