import re
from pathlib import Path

import pytest
from pydantic import AnyHttpUrl, AnyUrl, TypeAdapter, ValidationError

from kpops.config import (
    KafkaConnectConfig,
    KafkaRestConfig,
    KpopsConfig,
    SchemaRegistryConfig,
    get_config,
    set_config,
)

RESOURCES_PATH = Path(__file__).parent / "cli" / "resources"


def test_kpops_config_with_default_values():
    default_config = KpopsConfig(kafka_brokers="http://broker:9092")

    assert (
        default_config.topic_name_config.default_output_topic_name
        == "${pipeline.name}-${component.name}"
    )
    assert (
        default_config.topic_name_config.default_error_topic_name
        == "${pipeline.name}-${component.name}-error"
    )
    assert default_config.schema_registry.enabled is False
    assert default_config.schema_registry.url == AnyUrl("http://localhost:8081")
    assert default_config.kafka_rest.url == AnyUrl("http://localhost:8082")
    assert default_config.kafka_connect.url == AnyUrl("http://localhost:8083")
    assert default_config.kafka_rest.timeout == 30
    assert default_config.kafka_connect.timeout == 30
    assert default_config.schema_registry.timeout == 30
    assert default_config.create_namespace is False
    assert default_config.helm_config.context is None
    assert default_config.helm_config.debug is False
    assert default_config.helm_config.api_version is None
    assert default_config.helm_diff_config.ignore == set()
    assert default_config.retain_clean_jobs is False


def test_kpops_config_with_different_invalid_urls():
    with pytest.raises(ValidationError):
        KpopsConfig(
            kafka_brokers="http://broker:9092",
            kafka_connect=KafkaConnectConfig(
                url=TypeAdapter(AnyHttpUrl).validate_python("invalid-host")  # pyright: ignore[reportCallIssue,reportArgumentType]
            ),
        )

    with pytest.raises(ValidationError):
        KpopsConfig(
            kafka_brokers="http://broker:9092",
            kafka_rest=KafkaRestConfig(
                url=TypeAdapter(AnyHttpUrl).validate_python("invalid-host")  # pyright: ignore[reportCallIssue,reportArgumentType]
            ),
        )

    with pytest.raises(ValidationError):
        KpopsConfig(
            kafka_brokers="http://broker:9092",
            schema_registry=SchemaRegistryConfig(
                enabled=True,
                url=TypeAdapter(AnyHttpUrl).validate_python("invalid-host"),  # pyright: ignore[reportCallIssue,reportArgumentType]
            ),
        )


def test_global_kpops_config_not_initialized_error():
    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "KpopsConfig has not been initialized, call KpopsConfig.create() first."
        ),
    ):
        get_config()


def test_create_global_kpops_config():
    config = KpopsConfig.create(RESOURCES_PATH)
    assert get_config() == config


def test_set_global_kpops_config():
    config = KpopsConfig(
        kafka_brokers="broker:9092",
    )
    set_config(config)
    assert get_config() == config
