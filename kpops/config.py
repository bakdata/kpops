from __future__ import annotations

from pathlib import Path

from pydantic import AnyHttpUrl, Field, TypeAdapter
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmConfig, HelmDiffConfig
from kpops.utils.docstring import describe_object
from kpops.utils.pydantic import YamlConfigSettingsSource

ENV_PREFIX = "KPOPS_"


class TopicNameConfig(BaseSettings):
    """Configure the topic name variables you can use in the pipeline definition."""

    default_output_topic_name: str = Field(
        default="${pipeline.name}-${component.name}",
        description="Configures the value for the variable ${output_topic_name}",
    )
    default_error_topic_name: str = Field(
        default="${pipeline.name}-${component.name}-error",
        description="Configures the value for the variable ${error_topic_name}",
    )


class SchemaRegistryConfig(BaseSettings):
    """Configuration for Schema Registry."""

    enabled: bool = Field(
        default=False,
        description="Whether the Schema Registry handler should be initialized.",
    )
    url: AnyHttpUrl = Field(
        default=TypeAdapter(AnyHttpUrl).validate_python("http://localhost:8081"),
        description="Address of the Schema Registry.",
    )


class KafkaRestConfig(BaseSettings):
    """Configuration for Kafka REST Proxy."""

    url: AnyHttpUrl = Field(
        default=TypeAdapter(AnyHttpUrl).validate_python("http://localhost:8082"),
        description="Address of the Kafka REST Proxy.",
    )


class KafkaConnectConfig(BaseSettings):
    """Configuration for Kafka Connect."""

    url: AnyHttpUrl = Field(
        default=TypeAdapter(AnyHttpUrl).validate_python("http://localhost:8083"),
        description="Address of Kafka Connect.",
    )


class KpopsConfig(BaseSettings):
    """Global configuration for KPOps project."""

    defaults_path: Path = Field(
        default=Path(),
        examples=["defaults", "."],
        description="The path to the folder containing the defaults.yaml file and the environment defaults files. "
        "Paths can either be absolute or relative to `config.yaml`",
    )
    components_module: str | None = Field(
        default=None,
        description="Custom Python module defining project-specific KPOps components",
    )
    pipeline_base_dir: Path = Field(
        default=Path(),
        description="Base directory to the pipelines (default is current working directory)",
    )
    kafka_brokers: str = Field(
        default=...,
        examples=[
            "broker1:9092,broker2:9092,broker3:9092",
        ],
        description="The comma separated Kafka brokers address.",
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
        description="Whether to retain clean up jobs in the cluster or uninstall the, after completion.",
    )

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, env_nested_delimiter="__")

    @override
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ):
        return (
            env_settings,
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )
