from pathlib import Path

import pytest
from pydantic import AnyHttpUrl, ValidationError, parse_obj_as

from kpops.cli.config import (
    KafkaConnectConfig,
    KafkaRestConfig,
    KpopsConfig,
    SchemaRegistryConfig,
)


def test_kpops_config_with_default_values():
    default_config = KpopsConfig(
        environment="development", kafka_brokers="http://broker:9092"
    )

    assert default_config.defaults_path == Path(".")
    assert default_config.defaults_filename_prefix == "defaults"
    assert (
        default_config.topic_name_config.default_output_topic_name
        == "${pipeline_name}-${component_name}"
    )
    assert (
        default_config.topic_name_config.default_error_topic_name
        == "${pipeline_name}-${component_name}-error"
    )
    assert default_config.schema_registry.enabled is False
    assert default_config.schema_registry.url == "http://localhost:8081"
    assert default_config.kafka_rest.url == "http://localhost:8082"
    assert default_config.kafka_connect.url == "http://localhost:8083"
    assert default_config.timeout == 300
    assert default_config.create_namespace is False
    assert default_config.helm_config.context is None
    assert default_config.helm_config.debug is False
    assert default_config.helm_config.api_version is None
    assert default_config.helm_diff_config.ignore == set()
    assert default_config.retain_clean_jobs is False


def test_kpops_config_with_different_invalid_urls():
    with pytest.raises(ValidationError):
        KpopsConfig(
            environment="development",
            kafka_brokers="http://broker:9092",
            kafka_connect=KafkaConnectConfig(
                url=parse_obj_as(AnyHttpUrl, "in-valid-host")
            ),
        )

    with pytest.raises(ValidationError):
        KpopsConfig(
            environment="development",
            kafka_brokers="http://broker:9092",
            kafka_rest=KafkaRestConfig(url=parse_obj_as(AnyHttpUrl, "in-valid-host")),
        )

    with pytest.raises(ValidationError):
        KpopsConfig(
            environment="development",
            kafka_brokers="http://broker:9092",
            schema_registry=SchemaRegistryConfig(
                enabled=True,
                url=parse_obj_as(AnyHttpUrl, "in-valid-host"),
            ),
        )
