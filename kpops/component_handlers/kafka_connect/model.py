from enum import Enum
from typing import Any, Literal

from pydantic import BaseConfig, BaseModel, Extra, Field
from typing_extensions import override

from kpops.utils.docstring import describe_object
from kpops.utils.pydantic import CamelCaseConfig, DescConfig

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class KafkaConnectorType(str, Enum):
    SINK = "sink"
    SOURCE = "source"


class KafkaConnectorConfig(BaseModel):
    """Settings specific to Kafka Connectors"""

    connector_class: str = Field(default=..., alias="connector.class")
    name: str | None = None  # TODO: required

    class Config(DescConfig):
        extra = Extra.allow

        @override
        @staticmethod
        def schema_extra(schema: dict[str, Any], model: type[BaseModel]) -> None:
            schema["description"] = describe_object(model.__doc__)
            schema["additionalProperties"] = {"type": "string"}

    @property
    def class_name(self) -> str:
        return self.connector_class.split(".")[-1]

    def with_name(self, connector_name: str) -> Self:
        if self.name and self.name != connector_name:
            raise ValueError("Connector name should be the same as component name")
        self.name = connector_name
        return self

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
