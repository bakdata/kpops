from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError
from pytest_mock import MockerFixture

from kpops.components.common.topic import KafkaTopic, TopicConfig
from kpops.core.exception import ValidationError
from kpops.manifests.strimzi.kafka_topic import StrimziKafkaTopic, TopicSpec


@pytest.fixture
def kafka_topic() -> KafkaTopic:
    return KafkaTopic(
        name="test-topic",
        config=TopicConfig.model_validate(
            {
                "partitions_count": 3,
                "replication_factor": 2,
                "configs": {"cleanup.policy": "compact"},
            },
        ),
    )


def test_topic_spec_defaults():
    spec = TopicSpec()
    assert spec.partitions == 1
    assert spec.replicas == 1
    assert spec.config is None


def test_topic_spec_custom_values():
    spec = TopicSpec(partitions=3, replicas=2, config={"retention.ms": "60000"})
    assert spec.partitions == 3
    assert spec.replicas == 2
    assert spec.config == {"retention.ms": "60000"}


def test_topic_spec_validation():
    with pytest.raises(PydanticValidationError):
        TopicSpec(partitions=0)  # Less than 1, should raise validation error

    with pytest.raises(PydanticValidationError):
        TopicSpec(replicas=40000)  # Exceeds max value, should raise validation error


def test_strimzi_kafka_topic_from_topic(kafka_topic: KafkaTopic, mocker: MockerFixture):
    mock_config = MagicMock()
    mock_config.strimzi_topic.cluster_labels = ("bakdata.com/cluster", "my-cluster")
    mock_config.strimzi_topic.namespace = None
    mocker.patch(
        "kpops.manifests.strimzi.kafka_topic.get_config", return_value=mock_config
    )

    strimzi_topic = StrimziKafkaTopic.from_topic(kafka_topic)

    # Check metadata
    assert strimzi_topic.metadata.name == kafka_topic.name
    assert strimzi_topic.metadata.labels == {"bakdata.com/cluster": "my-cluster"}
    assert strimzi_topic.metadata.namespace is None

    # Check spec
    assert strimzi_topic.spec.partitions == kafka_topic.config.partitions_count
    assert strimzi_topic.spec.replicas == kafka_topic.config.replication_factor
    assert strimzi_topic.spec.config == kafka_topic.config.configs


def test_strimzi_kafka_topic_from_topic_with_namespace(
    kafka_topic: KafkaTopic, mocker: MockerFixture
):
    mock_config = MagicMock()
    mock_config.strimzi_topic.cluster_labels = ("bakdata.com/cluster", "my-cluster")
    mock_config.strimzi_topic.namespace = "strimzi"
    mocker.patch(
        "kpops.manifests.strimzi.kafka_topic.get_config", return_value=mock_config
    )

    strimzi_topic = StrimziKafkaTopic.from_topic(kafka_topic)

    # Check metadata
    assert strimzi_topic.metadata.name == kafka_topic.name
    assert strimzi_topic.metadata.labels == {"bakdata.com/cluster": "my-cluster"}
    assert strimzi_topic.metadata.namespace == "strimzi"

    # Check spec
    assert strimzi_topic.spec.partitions == kafka_topic.config.partitions_count
    assert strimzi_topic.spec.replicas == kafka_topic.config.replication_factor
    assert strimzi_topic.spec.config == kafka_topic.config.configs


def test_strimzi_kafka_topic_missing_config(kafka_topic, mocker):
    mock_config = MagicMock()
    mock_config.strimzi_topic = None
    mocker.patch(
        "kpops.manifests.strimzi.kafka_topic.get_config", return_value=mock_config
    )

    with pytest.raises(
        ValidationError,
        match="When manifesting KafkaTopic you must define 'strimzi_topic.label' in the config.yaml",
    ):
        StrimziKafkaTopic.from_topic(kafka_topic)
