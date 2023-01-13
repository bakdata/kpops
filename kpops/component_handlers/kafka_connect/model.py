from enum import Enum
from typing import Literal

from pydantic import BaseConfig, BaseModel, Extra, Field

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.utils.pydantic import CamelCaseConfig


class KafkaConnectorType(str, Enum):
    SINK = "sink"
    SOURCE = "source"


class KafkaConnectConfig(BaseModel):
    class Config(BaseConfig):
        extra = Extra.allow


class ConnectorTask(BaseModel):
    connector: str
    task: int


class KafkaConnectResponse(BaseModel):
    name: str
    config: dict[str, str]
    tasks: list[ConnectorTask]
    type: str | None

    class Config(BaseConfig):
        extra = Extra.forbid


class KafkaConnectConfigError(BaseModel):
    name: str
    errors: list[str]


class KafkaConnectConfigDescription(BaseModel):
    value: KafkaConnectConfigError


class KafkaConnectConfigErrorResponse(BaseModel):
    name: str
    error_count: int
    configs: list[KafkaConnectConfigDescription]


class KafkaConnectResetterHelmConfig(BaseModel):
    helm_config: HelmRepoConfig = Field(
        default=HelmRepoConfig(
            repository_name="bakdata-kafka-connect-resetter",
            url="https://bakdata.github.io/kafka-connect-resetter/",
        ),
        description="Configuration of Kafka connect resetter Helm Chart",
    )
    version: str = "1.0.4"
    helm_values: dict = Field(
        default_factory=dict,
        description="Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
    )
    namespace: str = Field("")


class KafkaConnectResetterConfig(BaseModel):
    brokers: str
    connector: str
    delete_consumer_group: bool | None = None
    offset_topic: str | None = None

    class Config(CamelCaseConfig):
        pass


class KafkaConnectResetterValues(BaseModel):
    connector_type: Literal["source", "sink"]
    config: KafkaConnectResetterConfig
    name_override: str

    class Config(CamelCaseConfig):
        pass

    def dict(self, **_) -> dict:
        return super().dict(by_alias=True, exclude_none=True)
