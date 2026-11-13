from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum, auto
from typing import Annotated, Any, ClassVar, Literal

import pydantic
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kpops.utils.pydantic import DescConfigModel, KeyValueConfigModel, Templatable


class OutputTopicTypes(StrEnum):
    """Types of output topic.

    - OUTPUT: output topic
    - ERROR: error topic
    """

    OUTPUT = auto()
    ERROR = auto()


class KafkaTopicConfigs(KeyValueConfigModel):
    """Kafka topic-level configs.

    Topic config reference: https://docs.confluent.io/platform/current/installation/configuration/topic-configs.html
    Configs that are not listed here can still be set and are passed through as is.

    :param cleanup_policy: The retention policy to use on log segments. `delete` (default) discards old segments when their retention time or size limit has been reached. `compact` enables log compaction, which retains the latest value for each key. Both can be combined as a comma-separated list, e.g. `delete,compact`.
    :param compression_type: The final compression type for the topic. Accepts the standard codecs (`gzip`, `snappy`, `lz4`, `zstd`), `uncompressed` for no compression, and `producer` to retain the original compression codec set by the producer.
    :param compression_gzip_level: The compression level to use if `compression.type` is set to `gzip`.
    :param compression_lz4_level: The compression level to use if `compression.type` is set to `lz4`.
    :param compression_zstd_level: The compression level to use if `compression.type` is set to `zstd`.
    :param delete_retention_ms: The amount of time in milliseconds to retain delete tombstone markers for log compacted topics. This also bounds the time in which a consumer must complete a read starting from offset 0 to get a valid snapshot of the final state.
    :param file_delete_delay_ms: The time in milliseconds to wait before deleting a file from the filesystem.
    :param flush_messages: The number of messages after which an fsync of data written to the log is forced. It is generally recommended to not set this and to rely on replication for durability and the operating system's background flush.
    :param flush_ms: The time interval in milliseconds after which an fsync of data written to the log is forced. It is generally recommended to not set this and to rely on replication for durability and the operating system's background flush.
    :param index_interval_bytes: How frequently, in bytes, Kafka adds entries to its offset index. More frequent indexing allows reads to jump closer to the exact position in the log but results in larger index files.
    :param local_retention_bytes: The maximum size of local log segments that can grow for a partition before old segments are deleted. The default of `-2` means that the value of `retention.bytes` is used. Tiered storage only.
    :param local_retention_ms: The time in milliseconds to keep local log segments before they are deleted. The default of `-2` means that the value of `retention.ms` is used. Tiered storage only.
    :param max_compaction_lag_ms: The maximum time in milliseconds a message remains ineligible for compaction in the log. Only applicable for compacted logs.
    :param max_message_bytes: The largest record batch size allowed by Kafka (after compression, if enabled).
    :param message_downconversion_enable: Whether to enable down-conversion of message formats for consumers. Deprecated: this is a no-op in Apache Kafka 4.0 and newer.
    :param message_timestamp_after_max_ms: The maximum allowed difference in milliseconds between the message timestamp and the broker's timestamp when the message timestamp is later. Ignored if `message.timestamp.type` is `LogAppendTime`.
    :param message_timestamp_before_max_ms: The maximum allowed difference in milliseconds between the broker's timestamp and the message timestamp when the message timestamp is earlier. Ignored if `message.timestamp.type` is `LogAppendTime`.
    :param message_timestamp_type: Whether the timestamp in the message is the message create time (`CreateTime`) or the log append time (`LogAppendTime`).
    :param min_cleanable_dirty_ratio: How frequently the log compactor attempts to clean the log, expressed as the ratio of dirty log to total log. A higher ratio means fewer, more efficient cleanings but more wasted space in the log.
    :param min_compaction_lag_ms: The minimum time in milliseconds a message remains uncompacted in the log. Only applicable for compacted logs.
    :param min_insync_replicas: The minimum number of in-sync replicas (including the leader) required for a write to succeed when a producer sets `acks` to `all` (or `-1`).
    :param preallocate: Whether to preallocate the file on disk when creating a new log segment.
    :param remote_log_copy_disable: Whether tiered data for the topic becomes read only, with no more data uploaded. Once set, `local.retention.*` becomes irrelevant and all data expiration follows `retention.*`.
    :param remote_log_delete_on_disable: Whether tiered data should be deleted after tiered storage is disabled on the topic. Must be enabled when setting `remote.storage.enable` from true to false.
    :param remote_storage_enable: Whether to enable tiered storage for the topic. When disabling, `remote.log.delete.on.disable` must also be set to true.
    :param retention_bytes: The maximum size in bytes a partition can grow to before old log segments are discarded when using the `delete` retention policy. The limit is enforced per partition. By default there is no size limit.
    :param retention_ms: The maximum time in milliseconds a log is retained before old log segments are discarded when using the `delete` retention policy. If set to `-1`, no time limit is applied.
    :param segment_bytes: The segment file size for the log. A larger segment size means fewer files but less granular control over retention. The active segment is rolled once it reaches this size.
    :param segment_index_bytes: The size in bytes of the index that maps offsets to file positions. It is generally not necessary to change this setting.
    :param segment_jitter_ms: The maximum random jitter in milliseconds subtracted from the scheduled segment roll time to avoid thundering herds of segment rolling.
    :param segment_ms: The period of time in milliseconds after which Kafka forces the log to roll even if the segment file is not full, so that retention can delete or compact old data.
    :param unclean_leader_election_enable: Whether to allow replicas not in the ISR set to be elected as leader as a last resort, even though this may result in data loss.
    """

    cleanup_policy: str | None = None
    compression_type: (
        Templatable[
            Literal["uncompressed", "zstd", "lz4", "snappy", "gzip", "producer"]
        ]
        | None
    ) = None
    compression_gzip_level: Templatable[int] | None = None
    compression_lz4_level: Templatable[int] | None = None
    compression_zstd_level: Templatable[int] | None = None
    delete_retention_ms: Templatable[int] | None = None
    file_delete_delay_ms: Templatable[int] | None = None
    flush_messages: Templatable[int] | None = None
    flush_ms: Templatable[int] | None = None
    index_interval_bytes: Templatable[int] | None = None
    local_retention_bytes: Templatable[int] | None = None
    local_retention_ms: Templatable[int] | None = None
    max_compaction_lag_ms: Templatable[int] | None = None
    max_message_bytes: Templatable[int] | None = None
    message_downconversion_enable: Templatable[bool] | None = None
    message_timestamp_after_max_ms: Templatable[int] | None = None
    message_timestamp_before_max_ms: Templatable[int] | None = None
    message_timestamp_type: (
        Templatable[Literal["CreateTime", "LogAppendTime"]] | None
    ) = None
    min_cleanable_dirty_ratio: Templatable[float] | None = None
    min_compaction_lag_ms: Templatable[int] | None = None
    min_insync_replicas: Templatable[int] | None = None
    preallocate: Templatable[bool] | None = None
    remote_log_copy_disable: Templatable[bool] | None = None
    remote_log_delete_on_disable: Templatable[bool] | None = None
    remote_storage_enable: Templatable[bool] | None = None
    retention_bytes: Templatable[int] | None = None
    retention_ms: Templatable[int] | None = None
    segment_bytes: Templatable[int] | None = None
    segment_index_bytes: Templatable[int] | None = None
    segment_jitter_ms: Templatable[int] | None = None
    segment_ms: Templatable[int] | None = None
    unclean_leader_election_enable: Templatable[bool] | None = None


class TopicConfig(DescConfigModel):
    """Configure an output topic.

    :param type: Topic type
    :param key_schema: Key schema class name
    :param value_schema: Value schema class name
    :param partitions_count: Number of partitions into which the topic is divided
    :param replication_factor: Replication factor of the topic
    :param configs: Topic configs
    :param label: Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`
    """

    type: OutputTopicTypes | None = Field(default=None, title="Topic type")
    key_schema: str | None = Field(
        default=None,
        title="Key schema",
    )
    value_schema: str | None = Field(
        default=None,
        title="Value schema",
    )
    partitions_count: Templatable[int] | None = Field(
        default=None,
        title="Partitions count",
    )
    replication_factor: Templatable[int] | None = Field(
        default=None,
        title="Replication factor",
    )
    configs: KafkaTopicConfigs = KafkaTopicConfigs()
    label: str | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def extra_topic_label(self) -> Any:
        """Ensure that `cls.label` is used correctly, assign type if needed."""
        if self.type and self.label:
            msg = "Define `label` only if `type` is undefined"
            raise ValueError(msg)
        return self


class KafkaTopic(BaseModel):
    """Internal representation of a Kafka topic.

    Users configure topic name and config through the `ToSection` of a `PipelineComponent`

    :param name: Topic name
    :param config: Topic config
    """

    name: str
    config: TopicConfig = TopicConfig()

    @property
    def id(self) -> str:
        """Unique identifier of this topic."""
        return f"topic-{self.name}"

    @staticmethod
    def deduplicate(topics: Iterable[KafkaTopic]) -> list[KafkaTopic]:
        """Deduplicate an iterable of Kafka topics based on their name, overwriting previous ones."""
        return list({topic.name: topic for topic in topics}.values())


def deserialize_kafka_topic_from_str(
    topic: str | dict[str, str] | Any,
) -> KafkaTopic | dict[str, str]:
    if topic and isinstance(topic, str):
        return KafkaTopic(name=topic)
    if isinstance(topic, KafkaTopic | dict):
        return topic
    msg = f"Topic should be a valid {KafkaTopic.__name__} instance or topic name string"
    raise ValueError(msg)


def serialize_kafka_topic_to_str(topic: KafkaTopic) -> str:
    return topic.name


# Pydantic type for KafkaTopic that serializes to str, used for generating the correct JSON schema
KafkaTopicStr = Annotated[
    KafkaTopic,
    pydantic.WithJsonSchema({"type": "string"}),
    pydantic.BeforeValidator(deserialize_kafka_topic_from_str),
    pydantic.PlainSerializer(serialize_kafka_topic_to_str),
]
