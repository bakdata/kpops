from __future__ import annotations

import os
from pathlib import Path

import yaml
from attr import define, field

from kpops.component_handlers.helm_wrapper.model import HelmConfig, HelmDiffConfig
from kpops.utils.yaml_loading import load_yaml_file

ENV_PREFIX = "KPOPS_"


@define(kw_only=True)
class TopicNameConfig:
    default_output_topic_name: str = field(
        default="${pipeline_name}-${component_name}",
        # description="Configures the value for the variable ${output_topic_name}",
    )
    default_error_topic_name: str = field(
        default="${pipeline_name}-${component_name}-error",
        # description="Configures the value for the variable ${error_topic_name}",
    )


@define(kw_only=True)
class PipelineConfig:
    defaults_path: Path = field(
        # description="The path to the folder containing the defaults file and the environment defaults files.",
    )
    environment: str = field(
        # default_factory=lambda: os.environ[f"{ENV_PREFIX}ENVIRONMENT"],
        # example="development",
        # description="The environment you want to generate and deploy the pipeline to. "
        # "Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).",
    )
    broker: str = field(
        # default_factory=lambda: os.environ[f"{ENV_PREFIX}KAFKA_BROKER"],
        # description="The Kafka broker address.",
    )
    defaults_filename_prefix: str = field(
        default="defaults",
        # description="The name of the defaults file and the prefix of the defaults environment file.",
    )
    topic_name_config: TopicNameConfig = field(
        default=TopicNameConfig(),
        # description="Configure the topic name variables you can use in the pipeline definition.",
    )
    kafka_rest_host: str | None = field(
        default=os.environ.get(f"{ENV_PREFIX}REST_PROXY_HOST"),
        # example="http://localhost:8082",
        # description="Address to the rest proxy REST API.",
    )
    kafka_connect_host: str | None = field(
        default=None,
        # env=f"{ENV_PREFIX}CONNECT_HOST",
        # example="http://localhost:8083",
        # description="Address to the kafka connect REST API.",
    )
    timeout: int = field(
        default=300,
        # env=f"{ENV_PREFIX}TIMEOUT",
        # description="The timeout in seconds that specifies when actions like deletion or deploy timeout.",
    )
    pipeline_prefix: str = field(
        default="${pipeline_name}-",
        # env=f"{ENV_PREFIX}PIPELINE_PREFIX",
        # description="Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
    )

    create_namespace: bool = False
    helm_config: HelmConfig = HelmConfig()
    helm_diff_config: HelmDiffConfig = HelmDiffConfig()

    retain_clean_jobs: bool = field(
        default=False,
        # env=f"{ENV_PREFIX}RETAIN_CLEAN_JOBS",
        # description="Whether to retain clean up jobs in the cluster or uninstall the, after completion.",
    )
    schema_registry_url: str | None = field(
        default=None,
        # example="http://localhost:8081",
        # env=f"{ENV_PREFIX}SCHEMA_REGISTRY_URL",
        # description="The URL to schema registry.",
    )

    # TODO load config.yaml
    # class Config(BaseConfig):
    #     config_path: Path = Path("config.yaml")
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"

    #     @classmethod
    #     def customise_sources(
    #         cls,
    #         init_settings: SettingsSourceCallable,
    #         env_settings: SettingsSourceCallable,
    #         file_secret_settings: SettingsSourceCallable,
    #     ):
    #         return (
    #             init_settings,
    #             yaml_config_settings_source,
    #             env_settings,
    #             file_secret_settings,
    #         )

    @staticmethod
    def load_from_file(config_path: Path, defaults_path: Path) -> PipelineConfig:
        with open(config_path) as yaml_file:
            config: dict = yaml.safe_load(yaml_file.read())
            return PipelineConfig(defaults_path=defaults_path, **config)


# def yaml_config_settings_source(settings: PipelineConfig) -> dict | list:
#     path_to_config = settings.Config.config_path
#     if path_to_config.exists():
#         return load_yaml_file(path_to_config)
#     return {}
