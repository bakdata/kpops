from pathlib import Path

from pydantic import BaseConfig, BaseSettings, Field
from pydantic.env_settings import SettingsSourceCallable

from kpops.component_handlers.helm_wrapper.model import (
    HelmConfig,
    HelmDiffConfig,
    HelmRepoConfig,
)
from kpops.utils.yaml_loading import load_yaml_file

ENV_PREFIX = "KPOPS_"


class TopicNameConfig(BaseSettings):
    default_output_topic_name: str = Field(
        default="${pipeline_name}-${component_name}",
        description="Configures the value for the variable ${output_topic_name}",
    )
    default_error_topic_name: str = Field(
        default="${pipeline_name}-${component_name}-error",
        description="Configures the value for the variable ${error_topic_name}",
    )


class KafkaConnectResetterHelmConfig(BaseSettings):
    helm_config: HelmRepoConfig = Field(
        default=HelmRepoConfig(
            repository_name="bakdata-kafka-connect-resetter",
            url="https://bakdata.github.io/kafka-connect-resetter/",
        ),
        description="Configuration of Kafka connect resetter Helm Chart",
    )
    version: str = "1.0.4"
    helm_values: dict = Field(
        default={},
        description="Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
    )
    namespace: str = Field(default="")


class PipelineConfig(BaseSettings):
    defaults_path: Path = Field(
        default=...,
        description="The path to the folder containing the defaults file and the environment defaults files.",
    )
    environment: str = Field(
        default=...,
        env=f"{ENV_PREFIX}ENVIRONMENT",
        example="development",
        description="The environment you want to generate and deploy the pipeline to. "
        "Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).",
    )
    broker: str = Field(
        default=...,
        env=f"{ENV_PREFIX}KAFKA_BROKER",
        description="The kafka broker address.",
    )
    defaults_filename_prefix: str = Field(
        default="defaults",
        description="The name of the defaults file and the prefix of the defaults environment file.",
    )
    topic_name_config: TopicNameConfig = Field(
        default=TopicNameConfig(),
        description="Configure the topic name variables you can use in the pipeline definition.",
    )
    kafka_rest_host: str | None = Field(
        default=None,
        env=f"{ENV_PREFIX}REST_PROXY_HOST",
        example="http://localhost:8082",
        description="Address to the rest proxy REST API.",
    )
    kafka_connect_host: str | None = Field(
        default=None,
        env=f"{ENV_PREFIX}CONNECT_HOST",
        example="http://localhost:8083",
        description="Address to the kafka connect REST API.",
    )
    timeout: int = Field(
        default=300,
        env=f"{ENV_PREFIX}TIMEOUT",
        description="The timeout in seconds that specifies when actions like deletion or deploy timeout.",
    )
    pipeline_prefix: str = Field(
        default="${pipeline_name}-",
        env=f"{ENV_PREFIX}PIPELINE_PREFIX",
        description="Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
    )

    helm_config: HelmConfig = Field(default=HelmConfig())
    helm_diff_config: HelmDiffConfig = Field(default=HelmDiffConfig())

    streams_bootstrap_helm_config: HelmRepoConfig = Field(
        default=HelmRepoConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://bakdata.github.io/streams-bootstrap/",
        ),
        description="Configuration for Streams Bootstrap Helm Charts",
    )
    kafka_connect_resetter_config: KafkaConnectResetterHelmConfig = Field(
        default=KafkaConnectResetterHelmConfig(),
        description="Configuration of kafka connect resetter helm chart and values. "
        "This is used for cleaning/resettting Kafka connectors, see https://github.com/bakdata/kafka-connect-resetter",
    )
    retain_clean_jobs: bool = Field(
        default=False,
        env=f"{ENV_PREFIX}RETAIN_CLEAN_JOBS",
        description="Whether to retain clean up jobs in the cluster or uninstall the, after completion.",
    )
    schema_registry_url: str | None = Field(
        default=None,
        example="http://localhost:8081",
        env=f"{ENV_PREFIX}SCHEMA_REGISTRY_URL",
        description="The URL to schema registry.",
    )

    class Config(BaseConfig):
        config_path: Path = Path("config.yaml")
        env_file = ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ):
            return (
                init_settings,
                yaml_config_settings_source,
                env_settings,
                file_secret_settings,
            )


def yaml_config_settings_source(settings: PipelineConfig) -> dict | list:
    path_to_config = settings.Config.config_path
    if path_to_config.exists():
        return load_yaml_file(path_to_config)
    return {}
