from pathlib import Path

import pytest
from pydantic_core import Url

from kpops.api.exception import ValidationError as KpopsValidationError
from kpops.config import (
    KpopsConfig,
    StrimziTopicConfig,
    get_config,
    set_config,
)


def test_strimzi_topic_config_valid():
    """Test StrimziTopicConfig with valid input."""
    config = StrimziTopicConfig(label={"key": "value"})
    assert config.cluster_labels == ("key", "value")


def test_strimzi_topic_config_empty_label():
    """Test StrimziTopicConfig with an empty label."""
    with pytest.raises(
        KpopsValidationError,
        match="'strimzi_topic.label' must contain a single key-value pair.",
    ):
        StrimziTopicConfig(label={})


def test_strimzi_topic_config_multiple_labels(caplog):
    """Test StrimziTopicConfig with multiple labels."""
    config = StrimziTopicConfig(label={"key1": "value1", "key2": "value2"})
    assert config.cluster_labels == ("key1", "value1")
    assert "only reads the first entry" in caplog.text


def test_kpops_config_initialization():
    """Test KpopsConfig initialization with valid defaults."""
    config = KpopsConfig(
        kafka_brokers="broker1:9092,broker2:9092,broker3:9092",
        pipeline_base_dir=Path("/pipelines"),
    )
    assert config.kafka_brokers == "broker1:9092,broker2:9092,broker3:9092"
    assert config.pipeline_base_dir == Path("/pipelines")
    assert (
        config.topic_name_config.default_output_topic_name
        == "${pipeline.name}-${component.name}"
    )


def test_kpops_config_create():
    """Test KpopsConfig.create class method."""
    config_dir = Path()
    config = KpopsConfig.create(config_dir=config_dir, environment="dev", verbose=True)
    assert config.pipeline_base_dir == Path("tests/pipeline")  # Default value
    assert config.kafka_rest.url == Url("http://localhost:8082")


def test_get_config_uninitialized():
    """Test get_config raises an error if KpopsConfig is not initialized."""
    with pytest.raises(
        RuntimeError,
    ) as runtime_error:
        get_config()
    assert (
        str(runtime_error.value)
        == "KpopsConfig has not been initialized, call KpopsConfig.create() first."
    )


def test_set_and_get_config():
    """Test set_config and get_config functions."""
    config = KpopsConfig(kafka_brokers="broker:9092")
    set_config(config)
    retrieved_config = get_config()
    assert retrieved_config is config
