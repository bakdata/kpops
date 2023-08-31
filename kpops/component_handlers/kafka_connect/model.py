from enum import Enum
from typing import Any, Literal

from pydantic import BaseConfig, BaseModel, ConfigDict, Extra, Field, validator
from typing_extensions import override

from kpops.utils.pydantic import CamelCaseConfigModel, DescConfigModel, to_dot


class KafkaConnectorType(str, Enum):
    SINK = "sink"
    SOURCE = "source"


class KafkaConnectorConfig(DescConfigModel):
    """Settings specific to Kafka Connectors"""

    connector_class: str
    name: str = Field(
        default=...,
        json_schema_extra={
            "hidden_from_schema": True,
        },
    )

    model_config = ConfigDict(
        extra=Extra.allow,
        alias_generator=to_dot,
        #TODO(sujuka99): combine with ``json_schema_extra`` of ``DescCohnfigModel`` 
        json_schema_extra={"additional_properties": {"type": "string"}},
    )

    @validator("connector_class")
    def connector_class_must_contain_dot(cls, connector_class: str) -> str:
        if "." not in connector_class:
            raise ValueError(f"Invalid connector class {connector_class}")
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
    type: str | None = None

    model_config = ConfigDict(
        extra=Extra.forbid
    )


class KafkaConnectConfigError(BaseModel):
    name: str
    errors: list[str]


class KafkaConnectConfigDescription(BaseModel):
    value: KafkaConnectConfigError


class KafkaConnectConfigErrorResponse(BaseModel):
    name: str
    error_count: int
    configs: list[KafkaConnectConfigDescription]


class KafkaConnectResetterConfig(CamelCaseConfigModel):
    brokers: str
    connector: str
    delete_consumer_group: bool | None = None
    offset_topic: str | None = None


class KafkaConnectResetterValues(CamelCaseConfigModel):
    connector_type: Literal["source", "sink"]
    config: KafkaConnectResetterConfig
    name_override: str

    @override
    def dict(self, **_) -> dict[str, Any]:
        return super().dict(by_alias=True, exclude_none=True)
