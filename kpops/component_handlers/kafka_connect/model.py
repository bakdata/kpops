from enum import Enum
from typing import Any, Literal

import pydantic
from pydantic import (
    BaseModel,
    ConfigDict,
    SerializationInfo,
    field_validator,
    model_serializer,
)
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import override

from kpops.components.base_components.helm_app import HelmAppValues
from kpops.components.base_components.models.topic import KafkaTopic, KafkaTopicStr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    by_alias,
    exclude_by_value,
    to_dot,
)


class KafkaConnectorType(str, Enum):
    SINK = "sink"
    SOURCE = "source"


class KafkaConnectorConfig(DescConfigModel):
    """Settings specific to Kafka Connectors."""

    connector_class: str
    name: SkipJsonSchema[str]
    topics: list[KafkaTopicStr] = []
    topics_regex: str | None = None
    errors_deadletterqueue_topic_name: KafkaTopicStr | None = None

    @override
    @staticmethod
    def json_schema_extra(schema: dict[str, Any], model: type[BaseModel]) -> None:
        super(KafkaConnectorConfig, KafkaConnectorConfig).json_schema_extra(
            schema, model
        )
        schema["additional_properties"] = {"type": "string"}

    model_config = ConfigDict(
        extra="allow",
        alias_generator=to_dot,
        json_schema_extra=json_schema_extra,
        populate_by_name=True,
    )

    @field_validator("connector_class")
    @classmethod
    def connector_class_must_contain_dot(cls, connector_class: str) -> str:
        if "." not in connector_class:
            msg = f"Invalid connector class {connector_class}"
            raise ValueError(msg)
        return connector_class

    @pydantic.field_validator("topics", mode="before")
    @classmethod
    def deserialize_topics(cls, topics: Any) -> list[KafkaTopic] | None | Any:
        if isinstance(topics, str):
            return [KafkaTopic(name=topic_name) for topic_name in topics.split(",")]
        return topics

    @property
    def class_name(self) -> str:
        return self.connector_class.split(".")[-1]

    @pydantic.field_serializer("topics")
    def serialize_topics(self, topics: list[KafkaTopic]) -> str | None:
        if not topics:
            return None
        return ",".join(topic.name for topic in topics)

    # TODO(Ivan Yordanov): Currently hacky and potentially unsafe. Find cleaner solution
    @model_serializer(mode="wrap", when_used="always")
    def serialize_model(self, handler, info: SerializationInfo) -> dict[str, Any]:
        result = exclude_by_value(handler(self), None)
        return {by_alias(self, name): value for name, value in result.items()}


class ConnectorTask(BaseModel):
    connector: str
    task: int


class KafkaConnectResponse(BaseModel):
    name: str
    config: dict[str, str]
    tasks: list[ConnectorTask]
    type: str | None = None

    model_config = ConfigDict(extra="forbid")


class KafkaConnectConfigError(BaseModel):
    name: str
    errors: list[str]


class KafkaConnectConfigDescription(BaseModel):
    value: KafkaConnectConfigError


class KafkaConnectConfigErrorResponse(BaseModel):
    name: str
    error_count: int
    configs: list[KafkaConnectConfigDescription]


class KafkaConnectorResetterConfig(CamelCaseConfigModel):
    brokers: str
    connector: str
    delete_consumer_group: bool | None = None
    offset_topic: str | None = None


class KafkaConnectorResetterValues(HelmAppValues):
    connector_type: Literal["source", "sink"]
    config: KafkaConnectorResetterConfig
