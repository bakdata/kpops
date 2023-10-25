from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, BaseConfig, BaseSettings, Field, parse_obj_as
from pydantic.env_settings import SettingsSourceCallable

from kpops.component_handlers.helm_wrapper.model import HelmConfig, HelmDiffConfig
from kpops.utils.docstring import describe_object
from kpops.utils.yaml import load_yaml_file

ENV_PREFIX = "KPOPS_"


class TopicNameConfig(BaseSettings):
    """Configure the topic name variables you can use in the pipeline definition."""

    default_output_topic_name: str = Field(
        default="${pipeline_name}-${component_name}",
        description="Configures the value for the variable ${output_topic_name}",
    )
    default_error_topic_name: str = Field(
        default="${pipeline_name}-${component_name}-error",
        description="Configures the value for the variable ${error_topic_name}",
    )


class SchemaRegistryConfig(BaseSettings):
    """Configuration for Schema Registry."""

    enabled: bool = Field(
        default=False,
        description="Whether the Schema Registry handler should be initialized.",
    )
    url: AnyHttpUrl = Field(
        # For validating URLs use parse_obj_as
        # https://github.com/pydantic/pydantic/issues/1106
        default=parse_obj_as(AnyHttpUrl, "http://localhost:8081"),
        env=f"{ENV_PREFIX}SCHEMA_REGISTRY_URL",
        description="Address of the Schema Registry.",
    )


class KafkaRestConfig(BaseSettings):
    """Configuration for Kafka REST Proxy."""

    url: AnyHttpUrl = Field(
        default=parse_obj_as(AnyHttpUrl, "http://localhost:8082"),
        env=f"{ENV_PREFIX}KAFKA_REST_URL",
        description="Address of the Kafka REST Proxy.",
    )


class KafkaConnectConfig(BaseSettings):
    """Configuration for Kafka Connect."""

    url: AnyHttpUrl = Field(
        default=parse_obj_as(AnyHttpUrl, "http://localhost:8083"),
        env=f"{ENV_PREFIX}KAFKA_CONNECT_URL",
        description="Address of Kafka Connect.",
    )


class KpopsConfig(BaseSettings):
    """Pipeline configuration unrelated to the components."""

    defaults_path: Path = Field(
        default=Path(),
        example="defaults",
        description="The path to the folder containing the defaults.yaml file and the environment defaults files. "
        "Paths can either be absolute or relative to `config.yaml`",
    )
    environment: str = Field(
        default=...,
        env=f"{ENV_PREFIX}ENVIRONMENT",
        example="development",
        description="The environment you want to generate and deploy the pipeline to. "
        "Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).",
    )
    kafka_brokers: str = Field(
        default=...,
        env=f"{ENV_PREFIX}KAFKA_BROKERS",
        description="The comma separated Kafka brokers address.",
        example="broker1:9092,broker2:9092,broker3:9092",
    )
    defaults_filename_prefix: str = Field(
        default="defaults",
        description="The name of the defaults file and the prefix of the defaults environment file.",
    )
    topic_name_config: TopicNameConfig = Field(
        default=TopicNameConfig(),
        description=describe_object(TopicNameConfig.__doc__),
    )
    schema_registry: SchemaRegistryConfig = Field(
        default=SchemaRegistryConfig(),
        description=describe_object(SchemaRegistryConfig.__doc__),
    )
    kafka_rest: KafkaRestConfig = Field(
        default=KafkaRestConfig(),
        description=describe_object(KafkaRestConfig.__doc__),
    )
    kafka_connect: KafkaConnectConfig = Field(
        default=KafkaConnectConfig(),
        description=describe_object(KafkaConnectConfig.__doc__),
    )
    timeout: int = Field(
        default=300,
        env=f"{ENV_PREFIX}TIMEOUT",
        description="The timeout in seconds that specifies when actions like deletion or deploy timeout.",
    )
    create_namespace: bool = Field(
        default=False,
        description="Flag for `helm upgrade --install`. Create the release namespace if not present.",
    )
    helm_config: HelmConfig = Field(
        default=HelmConfig(),
        description="Global flags for Helm.",
    )
    helm_diff_config: HelmDiffConfig = Field(
        default=HelmDiffConfig(),
        description="Configure Helm Diff.",
    )
    retain_clean_jobs: bool = Field(
        default=False,
        env=f"{ENV_PREFIX}RETAIN_CLEAN_JOBS",
        description="Whether to retain clean up jobs in the cluster or uninstall the, after completion.",
    )

    class Config(BaseConfig):
        config_path = Path("config.yaml")
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ENV_PREFIX

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[
            SettingsSourceCallable | Callable[[KpopsConfig], dict[str, Any]], ...
        ]:
            return (
                env_settings,
                init_settings,
                yaml_config_settings_source,
                file_secret_settings,
            )


def yaml_config_settings_source(settings: KpopsConfig) -> dict[str, Any]:
    path_to_config = settings.Config.config_path
    if path_to_config.exists():
        if isinstance(source := load_yaml_file(path_to_config), dict):
            return source
        err_msg = f"{path_to_config} must be a mapping."
        raise TypeError(err_msg)
    return {}
