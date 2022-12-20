from enum import Enum

from pydantic import BaseConfig, BaseModel, Extra


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
