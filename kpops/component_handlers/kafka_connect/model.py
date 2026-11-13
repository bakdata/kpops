from enum import StrEnum, auto
from typing import Any, ClassVar, Literal, override

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

from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.utils.enum import UpperStrEnum
from kpops.utils.pydantic import (
    DescConfigModel,
    Templatable,
    by_alias,
    exclude_by_value,
    to_dot,
    to_str,
)


class KafkaConnectorConfig(DescConfigModel):
    """Settings specific to Kafka Connectors.

    Connector config reference: https://kafka.apache.org/documentation/#connectconfigs
    Configs that are not listed here can still be set and are passed through as is.

    :param connector_class: Name or alias of the class for this connector. Must be a subclass of org.apache.kafka.connect.connector.Connector.
    :param name: Globally unique name to use for this connector.
    :param tasks_max: Maximum number of tasks to use for this connector.
    :param key_converter: Converter class used to convert between Kafka Connect format and the serialized form that is written to Kafka. This controls the format of the keys in messages written to or read from Kafka. Examples of common formats include JSON and Avro.
    :param value_converter: Converter class used to convert between Kafka Connect format and the serialized form that is written to Kafka. This controls the format of the values in messages written to or read from Kafka. Examples of common formats include JSON and Avro.
    :param header_converter: HeaderConverter class used to convert between Kafka Connect format and the serialized form that is written to Kafka. This controls the format of the header values in messages written to or read from Kafka. By default, the SimpleHeaderConverter is used to serialize header values to strings and deserialize them by inferring the schemas.
    :param transforms: Comma-separated aliases for the transformations to be applied to records.
    :param predicates: Comma-separated aliases for the predicates used by transformations.
    :param config_action_reload: The action that Connect should take on the connector when changes in external configuration providers result in a change in the connector's configuration properties. `none` does nothing, `restart` restarts the connector with the updated configuration properties.
    :param errors_retry_timeout: The maximum duration in milliseconds that a failed operation will be reattempted. The default is 0, which means no retries will be attempted. Use -1 for infinite retries.
    :param errors_retry_delay_max_ms: The maximum duration in milliseconds between consecutive retry attempts. Jitter will be added to the delay once this limit is reached to prevent thundering herd issues.
    :param errors_tolerance: Behavior for tolerating errors during connector operation. `none` (default) signals that any error will result in an immediate connector task failure; `all` changes the behavior to skip over problematic records.
    :param errors_log_enable: If true, write each error and the details of the failed operation and problematic record to the Connect application log. This is false by default, so that only errors that are not tolerated are reported.
    :param errors_log_include_messages: Whether to include in the log the Connect record that resulted in a failure. This is false by default, which prevents record keys, values, and headers from being written to log files.
    """

    connector_class: str
    name: SkipJsonSchema[str]
    tasks_max: Templatable[int] | None = None
    key_converter: str | None = None
    value_converter: str | None = None
    header_converter: str | None = None
    transforms: str | None = None
    predicates: str | None = None
    config_action_reload: Templatable[Literal["none", "restart"]] | None = None
    errors_retry_timeout: Templatable[int] | None = None
    errors_retry_delay_max_ms: Templatable[int] | None = None
    errors_tolerance: Templatable[Literal["none", "all"]] | None = None
    errors_log_enable: Templatable[bool] | None = None
    errors_log_include_messages: Templatable[bool] | None = None

    @override
    @staticmethod
    def json_schema_extra(schema: dict[str, Any], model_cls: type[BaseModel]) -> None:
        super(KafkaConnectorConfig, KafkaConnectorConfig).json_schema_extra(
            schema, model_cls
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
        polymorphic_serialization=True,
    )

    @field_validator("connector_class")
    @classmethod
    def connector_class_must_contain_dot(cls, connector_class: str) -> str:
        if "." not in connector_class:
            msg = f"Invalid connector class {connector_class}"
            raise ValueError(msg)
        return connector_class

    @property
    def class_name(self) -> str:
        return self.connector_class.split(".")[-1]

    # TODO(Ivan Yordanov): Currently hacky and potentially unsafe. Find cleaner solution
    @model_serializer(mode="wrap", when_used="always")
    def serialize_model(
        self,
        default_serialize_handler: pydantic.SerializerFunctionWrapHandler,
        info: pydantic.SerializationInfo,
    ) -> dict[str, str]:
        result = exclude_by_value(default_serialize_handler(self), None)
        return {
            by_alias(self.__class__, name): to_str(value)
            for name, value in result.items()
        }


class KafkaSinkConnectorConfig(KafkaConnectorConfig):
    """Settings specific to Kafka sink connectors.

    :param topics: List of topics to consume, separated by commas. Only one of `topics` or `topics.regex` should be specified.
    :param topics_regex: Regular expression giving topics to consume. Under the hood, the regex is compiled to a `java.util.regex.Pattern`. Only one of `topics` or `topics.regex` should be specified.
    :param errors_deadletterqueue_topic_name: The name of the topic to be used as the dead letter queue (DLQ) for messages that result in an error when processed by this sink connector, or its transformations or converters. The topic name is blank by default, which means that no messages are to be recorded in the DLQ.
    :param errors_deadletterqueue_topic_replication_factor: Replication factor used to create the dead letter queue topic when it doesn't already exist.
    :param errors_deadletterqueue_context_headers_enable: If true, add headers containing error context to the messages written to the dead letter queue.
    """

    topics: list[KafkaTopicStr] = []
    topics_regex: str | None = None
    errors_deadletterqueue_topic_name: KafkaTopicStr | None = None
    errors_deadletterqueue_topic_replication_factor: Templatable[int] | None = None
    errors_deadletterqueue_context_headers_enable: Templatable[bool] | None = None

    @pydantic.field_validator("topics", mode="before")
    @classmethod
    def deserialize_topics(cls, topics: Any) -> list[KafkaTopic] | Any | None:
        if isinstance(topics, str):
            return [KafkaTopic(name=topic_name) for topic_name in topics.split(",")]
        return topics

    @pydantic.field_serializer("topics")
    def serialize_topics(self, topics: list[KafkaTopic]) -> str | None:
        if not topics:
            return None
        return ",".join(topic.name for topic in topics)


class KafkaSourceConnectorConfig(KafkaConnectorConfig):
    """Settings specific to Kafka source connectors.

    :param topic_creation_groups: Groups of configurations for topics created by source connectors.
    :param topic_creation_default_replication_factor: Replication factor for new topics created by this connector. Use -1 for the broker's default. Together with `topic.creation.default.partitions`, this enables topic creation for the connector if `topic.creation.enable` is set on the worker.
    :param topic_creation_default_partitions: Number of partitions for new topics created by this connector. Use -1 for the broker's default. Together with `topic.creation.default.replication.factor`, this enables topic creation for the connector if `topic.creation.enable` is set on the worker.
    :param exactly_once_support: `required` forces a preflight check to ensure the connector can provide exactly-once semantics with the given configuration. `requested` (default) skips this check. Requires exactly-once source support on the worker.
    :param transaction_boundary: Where producer transactions are committed. `poll` (default) commits a transaction for every batch of records a task provides to Connect. `interval` commits after a user-defined time interval. `connector` relies on connector-defined transaction boundaries, which not all connectors support.
    :param transaction_boundary_interval_ms: If `transaction.boundary` is `interval`, the interval in milliseconds for producer transaction commits by connector tasks. Defaults to the worker's `offset.flush.interval.ms`.
    :param offsets_storage_topic: The name of a separate offsets topic to use for this connector. If not specified, the worker's global offsets topic is used. Only applicable in distributed mode.
    """

    topic_creation_groups: str | None = None
    topic_creation_default_replication_factor: Templatable[int] | None = None
    topic_creation_default_partitions: Templatable[int] | None = None
    exactly_once_support: Templatable[Literal["requested", "required"]] | None = None
    transaction_boundary: (
        Templatable[Literal["poll", "interval", "connector"]] | None
    ) = None
    transaction_boundary_interval_ms: Templatable[int] | None = None
    offsets_storage_topic: KafkaTopicStr | None = None


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
    SINK = auto()
    SOURCE = auto()


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
