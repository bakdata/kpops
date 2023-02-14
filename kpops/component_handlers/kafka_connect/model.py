from enum import Enum
from typing import Literal

from apischema import serialize
from attr import define

from kpops.utils.pydantic import FromDictMixin


class KafkaConnectorType(str, Enum):
    SINK = "sink"
    SOURCE = "source"


@define(kw_only=True)
class KafkaConnectConfig:
    def __init__(self, **kwargs) -> None:  # allow extra fields passed as kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


@define(kw_only=True)
class ConnectorTask:
    connector: str
    task: int


@define(kw_only=True)
class KafkaConnectResponse(FromDictMixin):
    name: str
    config: dict[str, str]
    tasks: list[ConnectorTask]
    type: str | None


@define(kw_only=True)
class KafkaConnectConfigError:
    name: str
    errors: list[str]


@define(kw_only=True)
class KafkaConnectConfigDescription:
    value: KafkaConnectConfigError


@define(kw_only=True)
class KafkaConnectConfigErrorResponse:
    name: str
    error_count: int
    configs: list[KafkaConnectConfigDescription]


@define(kw_only=True)
class KafkaConnectResetterConfig:
    brokers: str
    connector: str
    delete_consumer_group: bool | None = None
    offset_topic: str | None = None

    # TODO: camelcase


@define(kw_only=True)
class KafkaConnectResetterValues:
    connector_type: Literal["source", "sink"]
    config: KafkaConnectResetterConfig
    name_override: str

    # TODO: camelcase

    def dict(self) -> dict:
        return serialize(self, exclude_none=True)
