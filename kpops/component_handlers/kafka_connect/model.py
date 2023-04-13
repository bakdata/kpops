from enum import Enum
from typing import Any, Literal

from pydantic import BaseConfig, BaseModel, Extra
from typing_extensions import override

from kpops.utils.pydantic import CamelCaseConfig, DescConfig
from kpops.utils.docstring import describe_class


class KafkaConnectorType(str, Enum):
    SINK = "sink"
    SOURCE = "source"


class KafkaConnectConfig(BaseModel):
    class Config(DescConfig):
        extra = Extra.allow
        @override
        @staticmethod
        def schema_extra(schema: dict[str, Any], model: type[BaseModel]):
            schema["description"] = describe_class(model)
            schema["additionalProperties"] = {"type": "string"}
        


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
    def dict(self, **_) -> dict:
        return super().dict(by_alias=True, exclude_none=True)
