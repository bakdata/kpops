from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseConfig, BaseSettings, Field

from kpops.component_handlers.helm_wrapper.model import HelmConfig, HelmDiffConfig
from kpops.utils.yaml_loading import load_yaml_file

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic.env_settings import SettingsSourceCallable

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
    brokers: str = Field(
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
        description="Configure the topic name variables you can use in the pipeline definition.",
    )
    schema_registry_url: str | None = Field(
        default=None,
        example="http://localhost:8081",
        env=f"{ENV_PREFIX}SCHEMA_REGISTRY_URL",
        description="Address of the Schema Registry.",
    )
    kafka_rest_host: str | None = Field(
        default=None,
        env=f"{ENV_PREFIX}REST_PROXY_HOST",
        example="http://localhost:8082",
        description="Address of the Kafka REST Proxy.",
    )
    kafka_connect_host: str | None = Field(
        default=None,
        env=f"{ENV_PREFIX}CONNECT_HOST",
        example="http://localhost:8083",
        description="Address of Kafka Connect.",
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

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[
            SettingsSourceCallable | Callable[[PipelineConfig], dict[str, Any]], ...
        ]:
            return (
                env_settings,
                init_settings,
                yaml_config_settings_source,
                file_secret_settings,
            )


def yaml_config_settings_source(settings: PipelineConfig) -> dict[str, Any]:
    path_to_config = settings.Config.config_path
    if path_to_config.exists():
        if isinstance(source := load_yaml_file(path_to_config), dict):
            return source
        err_msg = f"{path_to_config} must be a mapping."
        raise TypeError(err_msg)
    return {}
