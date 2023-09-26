from enum import Enum
from typing import Any, Literal

from pydantic import BaseConfig, BaseModel, Extra, Field, validator
from typing_extensions import override

from kpops.utils.pydantic import CamelCaseConfig, DescConfig, to_dot


class KafkaConnectorType(str, Enum):
    SINK = "sink"
    SOURCE = "source"


class KafkaConnectorConfig(BaseModel):
    """Settings specific to Kafka Connectors."""

    connector_class: str
    name: str = Field(default=..., hidden_from_schema=True)

    class Config(DescConfig):
        extra = Extra.allow
        alias_generator = to_dot

        @override
        @classmethod
        def schema_extra(cls, schema: dict[str, Any], model: type[BaseModel]) -> None:
            super().schema_extra(schema, model)
            schema["additionalProperties"] = {"type": "string"}

    @validator("connector_class")
    def connector_class_must_contain_dot(cls, connector_class: str) -> str:
        if "." not in connector_class:
            msg = f"Invalid connector class {connector_class}"
            raise ValueError(msg)
        return connector_class

    @property
    def class_name(self) -> str:
        return self.connector_class.split(".")[-1]

    @override
    def dict(self, **_) -> dict[str, Any]:
        return super().dict(by_alias=True, exclude_none=True)


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

    @override
    def dict(self, **_) -> dict[str, Any]:
        return super().dict(by_alias=True, exclude_none=True)
