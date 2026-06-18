from __future__ import annotations

import logging
from pathlib import Path
from typing import ClassVar

import pydantic
from pydantic import AnyHttpUrl, Field, PrivateAttr, TypeAdapter
from pydantic.json_schema import SkipJsonSchema
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmConfig
from kpops.core.exception import ValidationError
from kpops.core.operation import OperationMode
from kpops.utils.docstring import describe_object
from kpops.utils.pydantic import YamlConfigSettingsSource

ENV_PREFIX = "KPOPS_"

log = logging.getLogger("KPOpsConfig")


class StrimziTopicConfig(BaseSettings):
    """Configuration for Strimzi Kafka Topics."""

    label_: dict[str, str] = Field(
        alias="label",
        description="The label to identify the KafkaTopic resources managed by the Topic Operator. This does not have to be the name of the Kafka cluster. It can be the label assigned to the KafkaTopic resource. If you deploy more than one Topic Operator, the labels must be unique for each. That is, the operators cannot manage the same resources.",
    )

    namespace: str | None = Field(
        default=None,
        description="The namespace where the Topic Operator is running. This is the namespace where the KafkaTopic resources are created.",
    )

    @property
    def cluster_labels(self) -> tuple[str, str]:
        """Return the defined strimzi_topic.label as a tuple."""
        return next(iter(self.label_.items()))

    @pydantic.field_validator("label_", mode="after")
    @classmethod
    def label_validator(cls, label: dict[str, str]) -> dict[str, str]:
        if len(label) == 0:
            msg = "'strimzi_topic.label' must contain a single key-value pair."
            raise ValidationError(msg)
        if len(label) > 1:
            log.warning(
                "'strimzi_topic.label' only reads the first entry in the dictionary. Other defined labels will be ignored."
            )

        return label


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
    timeout: int | float = Field(
        default=30, description="Operation timeout in seconds."
    )


class KafkaRestConfig(BaseSettings):
    """Configuration for Kafka REST Proxy."""

    url: AnyHttpUrl = Field(
        default=TypeAdapter(AnyHttpUrl).validate_python("http://localhost:8082"),
        description="Address of the Kafka REST Proxy.",
    )
    timeout: int | float = Field(
        default=30, description="Operation timeout in seconds."
    )


class KafkaConnectConfig(BaseSettings):
    """Configuration for Kafka Connect."""

    url: AnyHttpUrl = Field(
        default=TypeAdapter(AnyHttpUrl).validate_python("http://localhost:8083"),
        description="Address of Kafka Connect.",
    )
    timeout: int | float = Field(
        default=30, description="Operation timeout in seconds."
    )


class KpopsConfig(BaseSettings):
    """Global configuration for KPOps project."""

    _instance: ClassVar[KpopsConfig | None] = PrivateAttr(None)

    pipeline_base_dir: Path = Field(
        default=Path(),
        description="Base directory to the pipelines (default is current working directory)",
    )
    kafka_brokers: str = Field(
        examples=[
            "broker1:9092,broker2:9092,broker3:9092",
        ],
        description="The comma separated Kafka brokers address.",
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
    create_namespace: bool = Field(
        default=False,
        description="Flag for `helm upgrade --install`. Create the release namespace if not present.",
    )
    helm_config: HelmConfig = Field(
        default=HelmConfig(),
        description="Global flags for Helm.",
    )
    retain_clean_jobs: bool = Field(
        default=False,
        description="Whether to retain clean up jobs in the cluster or uninstall the, after completion.",
    )
    strimzi_topic: StrimziTopicConfig | None = Field(
        default=None,
        description=describe_object(StrimziTopicConfig.__doc__),
    )
    operation_mode: SkipJsonSchema[OperationMode] = Field(
        default=OperationMode.MANAGED,
        description="The operation mode of KPOps (managed, manifest, argo).",
        exclude=True,
    )
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
        use_enum_values=True,
    )

    @classmethod
    def create(
        cls,
        config_dir: Path | None,
        dotenv: list[Path] | None = None,
        environment: str | None = None,
        verbose: bool = False,
        operation_mode: OperationMode | None = None,
    ) -> KpopsConfig:
        cls.setup_logging_level(verbose)
        if config_dir:
            YamlConfigSettingsSource.config_dir = config_dir
        if environment:
            YamlConfigSettingsSource.environment = environment
        cls._instance = KpopsConfig(
            _env_file=dotenv  # pyright: ignore[reportCallIssue]
        )
        if operation_mode:
            cls._instance.operation_mode = operation_mode
        return cls._instance

    @staticmethod
    def setup_logging_level(verbose: bool):
        logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)

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
        """Change the precedence of sources that the Pydantic settings are compiled from.

        Environment variables (`env_settings`) take precedence over command line flags (`init_settings`).
        Command line flags (`init_settings`) take precedence over settings from a
        config.yaml (`YamlConfigSettingsSource(settings_cls)`) and so forth.
        """
        return (
            env_settings,
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


def get_config() -> KpopsConfig:
    if not KpopsConfig._instance:
        msg = f"{KpopsConfig.__name__} has not been initialized, call {KpopsConfig.__name__}.{KpopsConfig.create.__name__}() first."
        raise RuntimeError(msg)
    return KpopsConfig._instance


def set_config(config: KpopsConfig) -> None:
    KpopsConfig._instance = config
