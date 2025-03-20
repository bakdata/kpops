from enum import StrEnum, auto
from typing import Any, ClassVar

import pydantic
from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    field_serializer,
    field_validator,
    model_serializer,
)
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import override

from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.utils.pydantic import (
    DescConfigModel,
    by_alias,
    exclude_by_value,
    to_dot,
    to_str,
)


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
        schema["additional_properties"] = {
            "type": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "boolean"},
                    {"type": "integer"},
                    {"type": "number"},
                ],
            }
        }

    model_config: ClassVar[ConfigDict] = ConfigDict(
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
    def serialize_model(
        self,
        default_serialize_handler: pydantic.SerializerFunctionWrapHandler,
        info: pydantic.SerializationInfo,
    ) -> dict[str, str]:
        result = exclude_by_value(default_serialize_handler(self), None)
        return {by_alias(self, name): to_str(value) for name, value in result.items()}


class UpperStrEnum(StrEnum):
    @override
    @staticmethod
    def _generate_next_value_(name: str, *args: Any, **kwargs: Any) -> str:
        return name.upper()


class ConnectorCurrentState(UpperStrEnum):
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    FAILED = auto()


class ConnectorNewState(StrEnum):
    RUNNING = auto()
    PAUSED = auto()

    @property
    def api_enum(self) -> ConnectorCurrentState:
        return ConnectorCurrentState[self.name]


class CreateConnector(BaseModel):
    config: KafkaConnectorConfig
    initial_state: ConnectorNewState | None = None

    @computed_field
    @property
    def name(self) -> str:
        return self.config.name

    @field_serializer("initial_state")
    def serialize_initial_state(self, initial_state: ConnectorNewState) -> str:
        return initial_state.api_enum.value


class ConnectorStatus(BaseModel):
    state: ConnectorCurrentState
    worker_id: str


class ConnectorTaskStatus(BaseModel):
    id: int
    state: ConnectorCurrentState
    worker_id: str


class KafkaConnectorType(StrEnum):
    SINK = "sink"
    SOURCE = "source"


class ConnectorStatusResponse(BaseModel):
    name: str
    connector: ConnectorStatus
    tasks: list[ConnectorTaskStatus]
    type: KafkaConnectorType

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class ConnectorTask(BaseModel):
    connector: str
    task: int


class ConnectorResponse(BaseModel):
    name: str
    config: KafkaConnectorConfig
    tasks: list[ConnectorTask]
    type: KafkaConnectorType

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class KafkaConnectConfigError(BaseModel):
    name: str
    errors: list[str]


class KafkaConnectConfigDescription(BaseModel):
    value: KafkaConnectConfigError


class KafkaConnectConfigErrorResponse(BaseModel):
    name: str
    error_count: int
    configs: list[KafkaConnectConfigDescription]
