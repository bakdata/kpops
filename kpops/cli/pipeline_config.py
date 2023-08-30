from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from kpops.cli.settings_sources import YamlConfigSettingsSource
from kpops.component_handlers.helm_wrapper.model import HelmConfig, HelmDiffConfig

ENV_PREFIX = "KPOPS_"


class TopicNameConfig(BaseSettings):
    """Configures topic names."""

    default_output_topic_name: str = Field(
        default="${pipeline_name}-${component_name}",
        description="Configures the value for the variable ${output_topic_name}",
    )
    default_error_topic_name: str = Field(
        default="${pipeline_name}-${component_name}-error",
        description="Configures the value for the variable ${error_topic_name}",
    )


class PipelineConfig(BaseSettings):
    """Pipeline configuration unrelated to the components."""

    defaults_path: Path = Field(
        default=Path("."),
        examples=["defaults", "."],
        description="The path to the folder containing the defaults.yaml file and the environment defaults files. "
        "Paths can either be absolute or relative to `config.yaml`",
    )
    environment: str = Field(
        default=...,
        examples=[
            "development",
            "production",
        ],
        description="The environment you want to generate and deploy the pipeline to. "
        "Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).",
    )
    brokers: str = Field(
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
        description="Configure the topic name variables you can use in the pipeline definition.",
    )
    schema_registry_url: str | None = Field(
        default=None,
        examples=[
            "http://localhost:8081",
        ],
        description="Address of the Schema Registry.",
    )
    kafka_rest_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices(f"{ENV_PREFIX}rest_proxy_host", "kafka_rest_host"),
        examples=[
            "http://localhost:8082",
        ],
        description="Address of the Kafka REST Proxy.",
    )
    kafka_connect_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices(f"{ENV_PREFIX}connect_host", "kafka_connect_host"),
        examples=[
            "http://localhost:8083",
        ],
        description="Address of Kafka Connect.",
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
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )
        
